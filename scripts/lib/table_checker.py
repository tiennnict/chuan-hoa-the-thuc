"""
Phase 6: Kiểm tra bảng cụm (Quốc hiệu, Nơi nhận-Chân ký):
- Đảm bảo border trong suốt (giữ trạng thái nếu đã trong suốt).
- Kiểm tra tổng width có vượt content width không. Vượt → thu nhỏ + flag.

Phase 7: Quét thành phần thể thức thiếu hoặc sai vị trí.
"""

from xml.etree import ElementTree as ET
from .xml_utils import parse_xml, write_xml_preserve_root_attrs, get_original_xml
from pathlib import Path
from typing import Dict, List, Optional, Set
import re


NS_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = f"{{{NS_W}}}"


# Page width A4 = 11906 twips
# Content width = page_width - left - right margin
def _compute_content_width(unpacked_dir: Path, section_idx: int = 0) -> int:
    """Lấy content width của section đầu tiên (portrait)."""
    doc_xml = Path(unpacked_dir) / 'word' / 'document.xml'
    tree = parse_xml(doc_xml)
    root = tree.getroot()
    body = root.find(f'{W}body')
    if body is None:
        return 8820  # default A4 với margins chuẩn

    sectPrs = list(body.iter(f'{W}sectPr'))
    if not sectPrs:
        return 8820

    sectPr = sectPrs[min(section_idx, len(sectPrs) - 1)]
    pgSz = sectPr.find(f'{W}pgSz')
    pgMar = sectPr.find(f'{W}pgMar')

    if pgSz is None or pgMar is None:
        return 8820

    page_w = int(pgSz.get(f'{W}w', '11906'))
    left = int(pgMar.get(f'{W}left', '1985'))
    right = int(pgMar.get(f'{W}right', '1134'))

    return page_w - left - right


def _get_table_width(tbl: ET.Element) -> int:
    """Tính total width của bảng (sum gridCol)."""
    tblGrid = tbl.find(f'{W}tblGrid')
    if tblGrid is None:
        # Thử lấy từ tblPr/tblW
        tblPr = tbl.find(f'{W}tblPr')
        if tblPr is not None:
            tblW = tblPr.find(f'{W}tblW')
            if tblW is not None:
                w_val = tblW.get(f'{W}w', '0')
                try:
                    return int(w_val)
                except ValueError:
                    pass
        return 0

    total = 0
    for gridCol in tblGrid.findall(f'{W}gridCol'):
        w = gridCol.get(f'{W}w', '0')
        try:
            total += int(w)
        except ValueError:
            pass
    return total


def _set_borders_none(tbl: ET.Element):
    """Đảm bảo borders của table trong suốt (nil).

    OOXML schema CT_TblPrBase yêu cầu thứ tự element nghiêm ngặt:
    tblStyle, tblpPr, tblOverlap, bidiVisual, tblStyleRowBandSize,
    tblStyleColBandSize, tblW, jc, tblCellSpacing, tblInd,
    tblBorders, shd, tblLayout, tblCellMar, tblLook, tblCaption,
    tblDescription, tblPrChange.

    Vì vậy tblBorders phải đặt SAU tblInd và TRƯỚC shd/tblLayout/tblCellMar/tblLook.
    """
    tblPr = tbl.find(f'{W}tblPr')
    if tblPr is None:
        tblPr = ET.Element(f'{W}tblPr')
        tbl.insert(0, tblPr)

    # Xóa tblBorders cũ
    for tb in tblPr.findall(f'{W}tblBorders'):
        tblPr.remove(tb)

    tblBorders = ET.Element(f'{W}tblBorders')
    for side in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        el = ET.SubElement(tblBorders, f'{W}{side}')
        el.set(f'{W}val', 'nil')

    # Tìm vị trí chèn: ngay TRƯỚC element đầu tiên thuộc nhóm "sau tblBorders"
    # Các tag sau tblBorders trong schema: shd, tblLayout, tblCellMar, tblLook,
    # tblCaption, tblDescription, tblPrChange.
    after_tags = {
        f'{W}shd', f'{W}tblLayout', f'{W}tblCellMar', f'{W}tblLook',
        f'{W}tblCaption', f'{W}tblDescription', f'{W}tblPrChange',
    }
    children = list(tblPr)
    insert_idx = len(children)  # mặc định cuối nếu không có element sau
    for j, child in enumerate(children):
        if child.tag in after_tags:
            insert_idx = j
            break
    tblPr.insert(insert_idx, tblBorders)


def _shrink_table(tbl: ET.Element, target_width: int):
    """Thu nhỏ table proportional về target_width."""
    current = _get_table_width(tbl)
    if current <= 0 or current <= target_width:
        return

    ratio = target_width / current
    # Cập nhật tblGrid
    tblGrid = tbl.find(f'{W}tblGrid')
    if tblGrid is not None:
        for gridCol in tblGrid.findall(f'{W}gridCol'):
            w = int(gridCol.get(f'{W}w', '0'))
            gridCol.set(f'{W}w', str(int(w * ratio)))

    # Cập nhật tblW (tổng)
    tblPr = tbl.find(f'{W}tblPr')
    if tblPr is not None:
        tblW = tblPr.find(f'{W}tblW')
        if tblW is not None:
            tblW.set(f'{W}w', str(target_width))
            tblW.set(f'{W}type', 'dxa')

    # Cập nhật width của từng cell
    for tr in tbl.findall(f'{W}tr'):
        for tc in tr.findall(f'{W}tc'):
            tcPr = tc.find(f'{W}tcPr')
            if tcPr is not None:
                tcW = tcPr.find(f'{W}tcW')
                if tcW is not None:
                    w = int(tcW.get(f'{W}w', '0'))
                    tcW.set(f'{W}w', str(int(w * ratio)))


def _table_contains(tbl: ET.Element, pattern: re.Pattern) -> bool:
    """Kiểm tra table có chứa text khớp pattern không."""
    texts = []
    for t in tbl.iter(f'{W}t'):
        if t.text:
            texts.append(t.text)
    joined = ' '.join(texts)
    return bool(pattern.search(joined))


def run_phase6(unpacked_dir, report: Dict) -> Dict:
    """Phase 6: kiểm tra và chuẩn hóa bảng cụm."""
    doc_xml = Path(unpacked_dir) / 'word' / 'document.xml'
    tree = parse_xml(doc_xml)
    root = tree.getroot()

    content_width = _compute_content_width(Path(unpacked_dir))

    re_quoc_hieu = re.compile(r'CỘNG\s*HO[ÀA]\s+XÃ\s+HỘI', re.IGNORECASE)
    re_noi_nhan = re.compile(r'Nơi\s+nhận\s*:', re.IGNORECASE)

    phase_report = {
        'content_width': content_width,
        'tables_processed': [],
        'tables_shrunk': [],
    }

    for tbl in list(root.iter(f'{W}tbl')):
        is_quoc_hieu = _table_contains(tbl, re_quoc_hieu)
        is_noi_nhan = _table_contains(tbl, re_noi_nhan)

        if not (is_quoc_hieu or is_noi_nhan):
            continue

        label = 'quoc_hieu_table' if is_quoc_hieu else 'noi_nhan_table'
        current_width = _get_table_width(tbl)

        entry = {
            'type': label,
            'width_before': current_width,
            'width_after': current_width,
            'shrunk': False,
        }

        # Đảm bảo border trong suốt
        _set_borders_none(tbl)

        # Kiểm tra vượt margin
        if current_width > content_width and content_width > 0:
            _shrink_table(tbl, content_width)
            entry['width_after'] = content_width
            entry['shrunk'] = True
            phase_report['tables_shrunk'].append(label)

        phase_report['tables_processed'].append(entry)

    write_xml_preserve_root_attrs(tree, doc_xml, get_original_xml(doc_xml.parent.parent, doc_xml.name))

    report['phase6'] = phase_report
    return report


# ============================================================
# PHASE 7: Flag thành phần thể thức thiếu
# ============================================================

REQUIRED_COMPONENTS_DEFAULT = {
    'quoc_hieu', 'tieu_ngu',
    'ten_co_quan_ban_hanh',
    'so_ky_hieu', 'dia_danh_ngay_thang',
    'trich_yeu',
    'chan_ky_chuc_vu', 'chan_ky_ho_ten',
    'noi_nhan_label',
}

# Văn bản không phải Công văn cần có tên loại
REQUIRED_FOR_NAMED_TYPES = {'ten_loai_van_ban'}


# Component name human-readable (cho báo cáo)
COMPONENT_VN_NAMES = {
    'quoc_hieu': 'Quốc hiệu',
    'tieu_ngu': 'Tiêu ngữ',
    'ten_co_quan_chu_quan': 'Tên cơ quan chủ quản',
    'ten_co_quan_ban_hanh': 'Tên cơ quan ban hành',
    'so_ky_hieu': 'Số, ký hiệu',
    'dia_danh_ngay_thang': 'Địa danh và ngày tháng',
    'ten_loai_van_ban': 'Tên loại văn bản',
    'trich_yeu': 'Trích yếu',
    'trich_yeu_cong_van': 'Trích yếu (Công văn)',
    'kinh_gui': 'Kính gửi',
    'chan_ky_quyen_han': 'Quyền hạn người ký',
    'chan_ky_chuc_vu': 'Chức vụ người ký',
    'chan_ky_ho_ten': 'Họ tên người ký',
    'noi_nhan_label': 'Nơi nhận (nhãn)',
    'noi_nhan_item': 'Nơi nhận (danh sách)',
}


def run_phase7(unpacked_dir, classifications: Dict[int, str],
               doc_type: str, report: Dict) -> Dict:
    """Phase 7: flag thành phần thiếu."""
    found_types: Set[str] = set(classifications.values())

    required = set(REQUIRED_COMPONENTS_DEFAULT)
    if doc_type != 'Công văn':
        required |= REQUIRED_FOR_NAMED_TYPES
    else:
        required |= {'trich_yeu_cong_van', 'kinh_gui'}

    missing = []
    for comp in required:
        if comp not in found_types:
            missing.append({
                'component': comp,
                'label': COMPONENT_VN_NAMES.get(comp, comp),
                'description': f'Không tìm thấy {COMPONENT_VN_NAMES.get(comp, comp)}',
            })

    order_warnings = _check_order(classifications)

    # Lấy nonstandard_flags từ report (được ghi vào bởi Phase 2)
    nonstandard_flags = report.get('nonstandard_flags', [])

    report['phase7'] = {
        'missing_components': missing,
        'order_warnings': order_warnings,
        'nonstandard_structure_flags': nonstandard_flags,
    }
    return report


def _check_order(classifications: Dict[int, str]) -> List[Dict]:
    """Kiểm tra thứ tự cơ bản của các thành phần thể thức."""
    warnings = []
    # Thứ tự kỳ vọng (rough): quoc_hieu/ten_co_quan trước số ký hiệu, trước tên loại,
    # trước nội dung, trước nơi nhận
    expected_order = {
        'quoc_hieu': 1, 'tieu_ngu': 1,
        'ten_co_quan_chu_quan': 1, 'ten_co_quan_ban_hanh': 1,
        'so_ky_hieu': 2, 'dia_danh_ngay_thang': 2,
        'ten_loai_van_ban': 3, 'trich_yeu': 3, 'trich_yeu_cong_van': 3,
        'kinh_gui': 4, 'can_cu': 4,
        'body': 5, 'heading_phan': 5, 'heading_chuong': 5,
        'heading_muc': 5, 'heading_tieu_muc': 5, 'heading_dieu': 5,
        'khoan_co_tieu_de': 5,
        'noi_nhan_label': 6, 'noi_nhan_item': 6,
        'chan_ky_quyen_han': 6, 'chan_ky_chuc_vu': 6, 'chan_ky_ho_ten': 6,
    }

    sorted_indices = sorted(classifications.keys())
    last_order = 0
    last_comp = None

    for idx in sorted_indices:
        comp = classifications[idx]
        order = expected_order.get(comp)
        if order is None:
            continue
        if order < last_order:
            warnings.append({
                'paragraph_index': idx,
                'component': comp,
                'label': COMPONENT_VN_NAMES.get(comp, comp),
                'description': (
                    f'{COMPONENT_VN_NAMES.get(comp, comp)} xuất hiện sau '
                    f'{COMPONENT_VN_NAMES.get(last_comp, last_comp)}, '
                    f'có thể sai thứ tự thể thức.'
                ),
            })
            break  # chỉ flag 1 lần để tránh nhiễu
        last_order = order
        last_comp = comp

    return warnings
