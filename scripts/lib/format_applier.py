"""
Phase 3: Áp định dạng (style-based hoặc direct formatting) lên từng paragraph
dựa trên component_type đã phân loại ở Phase 2.

Quy tắc:
- Headings, body, khoản, căn cứ, nơi nhận, ten_loai_van_ban, trich_yeu → pStyle.
- ten_loai_van_ban / trich_yeu / trich_yeu_cong_van → pStyle Title + direct override.
- Heading level thực tế được tính từ level_map (đẩy heading lên).
- Components xuất hiện 1 lần (Quốc hiệu, Tên cơ quan, Số ký hiệu, Kính gửi, Chân ký) → direct.
"""

from typing import Dict, Optional
from xml.etree import ElementTree as ET
from .xml_utils import parse_xml, write_xml_preserve_root_attrs, get_original_xml
from pathlib import Path


NS_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = f"{{{NS_W}}}"


def _sz(font_pair: int, type_: str) -> int:
    if font_pair == 14:
        sizes = {
            'quoc_hieu': 26, 'tieu_ngu': 28,
            'ten_co_quan_chu_quan': 26, 'ten_co_quan_ban_hanh': 26,
            'so_ky_hieu': 26, 'dia_danh_ngay_thang': 28,
            'ten_loai_van_ban': 28, 'trich_yeu': 28, 'trich_yeu_cong_van': 26,
            'kinh_gui': 28,
            'chan_ky_quyen_han': 28, 'chan_ky_chuc_vu': 28, 'chan_ky_ho_ten': 28,
            'noi_nhan_label': 24, 'noi_nhan_item': 22,
            'body': 28, 'heading': 28, 'can_cu': 28, 'khoan_co_tieu_de': 28,
            'phu_luc_label': 28, 'phu_luc_tieu_de': 28,
            'header': 28,
        }
    else:
        sizes = {
            'quoc_hieu': 24, 'tieu_ngu': 26,
            'ten_co_quan_chu_quan': 24, 'ten_co_quan_ban_hanh': 24,
            'so_ky_hieu': 26, 'dia_danh_ngay_thang': 26,
            'ten_loai_van_ban': 26, 'trich_yeu': 26, 'trich_yeu_cong_van': 24,
            'kinh_gui': 26,
            'chan_ky_quyen_han': 26, 'chan_ky_chuc_vu': 26, 'chan_ky_ho_ten': 26,
            'noi_nhan_label': 24, 'noi_nhan_item': 22,
            'body': 26, 'heading': 26, 'can_cu': 26, 'khoan_co_tieu_de': 26,
            'phu_luc_label': 26, 'phu_luc_tieu_de': 26,
            'header': 26,
        }
    return sizes.get(type_, sizes['body'])


# Mapping component_type → pStyle ID cơ sở (có thể bị ghi đè bởi level_map)
STYLE_MAP_BASE = {
    'body': 'Normal',
    'heading_phan': 'Heading1',
    'heading_chuong': 'Heading2',
    'heading_muc': 'Heading3',
    'heading_tieu_muc': 'Heading4',
    'heading_dieu': 'Heading5',
    'khoan_co_tieu_de': 'KhoanCoTieuDe',
    'can_cu': 'CanCu',
    'noi_nhan_label': 'NoiNhanLabel',
    'noi_nhan_item': 'NoiNhanItem',
    'ten_loai_van_ban': 'Title',
    'trich_yeu': 'Title',
    'trich_yeu_cong_van': 'Title',
}

# Mapping component_type → key trong level_map (để tính heading level thực)
COMP_TO_LEVEL_KEY = {
    'heading_phan': 'phan',
    'heading_chuong': 'chuong',
    'heading_muc': ('muc', 'muc_6b'),   # tuple: thử cả 2 key
    'heading_tieu_muc': 'tieu_muc',
    'heading_dieu': 'dieu',
    'khoan_co_tieu_de': 'khoan_co_tieu_de',
}

# Dùng pStyle-based (không direct)
STYLE_TYPES = set(STYLE_MAP_BASE.keys())

# Direct formatting
DIRECT_TYPES = {
    'quoc_hieu', 'tieu_nhu', 'tieu_ngu',
    'ten_co_quan_chu_quan', 'ten_co_quan_ban_hanh',
    'so_ky_hieu', 'dia_danh_ngay_thang',
    'kinh_gui',
    'chan_ky_quyen_han', 'chan_ky_chuc_vu', 'chan_ky_ho_ten',
    'phu_luc_label', 'phu_luc_tieu_de',
}


def _resolve_style_id(comp_type: str, level_map: Dict[str, int]) -> str:
    """
    Tính pStyle ID thực tế sau khi đẩy heading lên.
    Với heading: dùng level_map để lấy effective level.
    Với khoan_co_tieu_de: nếu có trong level_map (6b có heading) → Heading{N}, không → KhoanCoTieuDe.
    """
    if comp_type in ('ten_loai_van_ban', 'trich_yeu', 'trich_yeu_cong_van'):
        return 'Title'
    if comp_type in ('body', 'can_cu', 'noi_nhan_label', 'noi_nhan_item'):
        return STYLE_MAP_BASE[comp_type]

    level_key = COMP_TO_LEVEL_KEY.get(comp_type)
    if level_key is None:
        return STYLE_MAP_BASE.get(comp_type, 'Normal')

    if isinstance(level_key, tuple):
        # Thử cả 2 key
        level = None
        for k in level_key:
            if k in level_map:
                level = level_map[k]
                break
    else:
        level = level_map.get(level_key)

    if level is None:
        return STYLE_MAP_BASE.get(comp_type, 'Normal')

    return f'Heading{level}'


# --- Helpers cho pPr, rPr ---

def _ensure_pPr(p: ET.Element) -> ET.Element:
    """Đảm bảo p có <w:pPr>, trả về element."""
    pPr = p.find(f'{W}pPr')
    if pPr is None:
        pPr = ET.SubElement(p, f'{W}pPr')
        # pPr phải đứng đầu trong p
        p.remove(pPr)
        p.insert(0, pPr)
    return pPr


def _set_pStyle(pPr: ET.Element, style_id: str):
    """Set <w:pStyle w:val="..."/>. Element order: pStyle phải đầu pPr."""
    # Xóa pStyle cũ
    for old in pPr.findall(f'{W}pStyle'):
        pPr.remove(old)
    pStyle = ET.Element(f'{W}pStyle')
    pStyle.set(f'{W}val', style_id)
    pPr.insert(0, pStyle)


def _remove_direct_pPr_format(pPr: ET.Element):
    """
    Xóa direct formatting trong pPr để style chiếm ưu thế.
    Giữ pStyle, numPr, các phần đặc biệt.
    """
    to_remove = [f'{W}spacing', f'{W}ind', f'{W}jc', f'{W}keepNext',
                 f'{W}outlineLvl']
    for tag in to_remove:
        for el in pPr.findall(tag):
            pPr.remove(el)


def _remove_direct_rPr_format(rPr: ET.Element):
    """Xóa direct formatting trong rPr (chỉ cho phần body)."""
    to_remove = [f'{W}rFonts', f'{W}sz', f'{W}szCs', f'{W}b', f'{W}bCs',
                 f'{W}i', f'{W}iCs', f'{W}caps']
    for tag in to_remove:
        for el in rPr.findall(tag):
            rPr.remove(el)


def _set_run_format(rPr: ET.Element, font: str, sz: int, bold: bool,
                    italic: bool, caps: bool):
    """Set định dạng cho 1 run (đè lên rPr cũ)."""
    # Font
    for old in rPr.findall(f'{W}rFonts'):
        rPr.remove(old)
    rFonts = ET.SubElement(rPr, f'{W}rFonts')
    rFonts.set(f'{W}ascii', font)
    rFonts.set(f'{W}hAnsi', font)
    rFonts.set(f'{W}cs', font)

    # Size
    for old in rPr.findall(f'{W}sz'):
        rPr.remove(old)
    for old in rPr.findall(f'{W}szCs'):
        rPr.remove(old)
    sz_el = ET.SubElement(rPr, f'{W}sz')
    sz_el.set(f'{W}val', str(sz))
    szCs_el = ET.SubElement(rPr, f'{W}szCs')
    szCs_el.set(f'{W}val', str(sz))

    # Bold
    for old in rPr.findall(f'{W}b'):
        rPr.remove(old)
    for old in rPr.findall(f'{W}bCs'):
        rPr.remove(old)
    if bold:
        ET.SubElement(rPr, f'{W}b')
        ET.SubElement(rPr, f'{W}bCs')

    # Italic
    for old in rPr.findall(f'{W}i'):
        rPr.remove(old)
    for old in rPr.findall(f'{W}iCs'):
        rPr.remove(old)
    if italic:
        ET.SubElement(rPr, f'{W}i')
        ET.SubElement(rPr, f'{W}iCs')

    # Caps
    for old in rPr.findall(f'{W}caps'):
        rPr.remove(old)
    if caps:
        ET.SubElement(rPr, f'{W}caps')


def _set_pPr_direct(pPr: ET.Element, jc: Optional[str] = None,
                    first_line: Optional[int] = None,
                    spacing_before: Optional[int] = None,
                    spacing_after: Optional[int] = None,
                    line: Optional[int] = None,
                    keep_next: bool = False):
    """Set các thuộc tính pPr direct."""
    # Xóa cũ
    for tag in [f'{W}spacing', f'{W}ind', f'{W}jc', f'{W}keepNext']:
        for el in pPr.findall(tag):
            pPr.remove(el)

    # keepNext (phải trước spacing)
    if keep_next:
        ET.SubElement(pPr, f'{W}keepNext')

    # spacing
    if spacing_before is not None or spacing_after is not None or line is not None:
        spacing = ET.SubElement(pPr, f'{W}spacing')
        if spacing_before is not None:
            spacing.set(f'{W}before', str(spacing_before))
        if spacing_after is not None:
            spacing.set(f'{W}after', str(spacing_after))
        if line is not None:
            spacing.set(f'{W}line', str(line))
            spacing.set(f'{W}lineRule', 'auto')

    # ind
    if first_line is not None:
        ind = ET.SubElement(pPr, f'{W}ind')
        ind.set(f'{W}firstLine', str(first_line))

    # jc
    if jc:
        jc_el = ET.SubElement(pPr, f'{W}jc')
        jc_el.set(f'{W}val', jc)


def _apply_to_all_runs(p: ET.Element, font: str, sz: int, bold: bool,
                       italic: bool, caps: bool):
    """Áp định dạng cho TẤT CẢ run trong paragraph."""
    for r in p.findall(f'{W}r'):
        rPr = r.find(f'{W}rPr')
        if rPr is None:
            rPr = ET.SubElement(r, f'{W}rPr')
            r.remove(rPr)
            r.insert(0, rPr)
        _set_run_format(rPr, font, sz, bold, italic, caps)


def _apply_normalize_run_size(p: ET.Element, sz: int):
    """
    Chỉ chuẩn hóa cỡ chữ (cho body): set sz cho mọi run mà không đụng b/i/caps.
    Dùng cho components áp pStyle nhưng vẫn cần đảm bảo cỡ chữ đúng cặp.
    """
    for r in p.findall(f'{W}r'):
        rPr = r.find(f'{W}rPr')
        if rPr is None:
            rPr = ET.SubElement(r, f'{W}rPr')
            r.remove(rPr)
            r.insert(0, rPr)
        # Set sz
        for old in rPr.findall(f'{W}sz'):
            rPr.remove(old)
        for old in rPr.findall(f'{W}szCs'):
            rPr.remove(old)
        sz_el = ET.SubElement(rPr, f'{W}sz')
        sz_el.set(f'{W}val', str(sz))
        szCs_el = ET.SubElement(rPr, f'{W}szCs')
        szCs_el.set(f'{W}val', str(sz))


# --- Direct formatting per component ---

def _apply_quoc_hieu(p: ET.Element, font_pair: int):
    pPr = _ensure_pPr(p)
    _remove_direct_pPr_format(pPr)
    _set_pPr_direct(pPr, jc='center', first_line=0,
                    spacing_before=0, spacing_after=0, line=240)
    _apply_to_all_runs(p, 'Times New Roman', _sz(font_pair, 'quoc_hieu'),
                       bold=True, italic=False, caps=True)


def _apply_tieu_ngu(p: ET.Element, font_pair: int):
    pPr = _ensure_pPr(p)
    _remove_direct_pPr_format(pPr)
    _set_pPr_direct(pPr, jc='center', first_line=0,
                    spacing_before=0, spacing_after=0, line=240)
    _apply_to_all_runs(p, 'Times New Roman', _sz(font_pair, 'tieu_ngu'),
                       bold=True, italic=False, caps=False)


def _apply_ten_co_quan_chu_quan(p: ET.Element, font_pair: int):
    pPr = _ensure_pPr(p)
    _remove_direct_pPr_format(pPr)
    _set_pPr_direct(pPr, jc='center', first_line=0,
                    spacing_before=0, spacing_after=0, line=240)
    _apply_to_all_runs(p, 'Times New Roman', _sz(font_pair, 'ten_co_quan_chu_quan'),
                       bold=False, italic=False, caps=True)


def _apply_ten_co_quan_ban_hanh(p: ET.Element, font_pair: int):
    pPr = _ensure_pPr(p)
    _remove_direct_pPr_format(pPr)
    _set_pPr_direct(pPr, jc='center', first_line=0,
                    spacing_before=0, spacing_after=0, line=240)
    _apply_to_all_runs(p, 'Times New Roman', _sz(font_pair, 'ten_co_quan_ban_hanh'),
                       bold=True, italic=False, caps=True)


def _apply_so_ky_hieu(p: ET.Element, font_pair: int):
    pPr = _ensure_pPr(p)
    _remove_direct_pPr_format(pPr)
    _set_pPr_direct(pPr, jc='center', first_line=0,
                    spacing_before=0, spacing_after=0, line=240)
    _apply_to_all_runs(p, 'Times New Roman', _sz(font_pair, 'so_ky_hieu'),
                       bold=False, italic=False, caps=False)


def _apply_dia_danh_ngay_thang(p: ET.Element, font_pair: int):
    pPr = _ensure_pPr(p)
    _remove_direct_pPr_format(pPr)
    _set_pPr_direct(pPr, jc='center', first_line=0,
                    spacing_before=0, spacing_after=0, line=240)
    _apply_to_all_runs(p, 'Times New Roman', _sz(font_pair, 'dia_danh_ngay_thang'),
                       bold=False, italic=True, caps=False)


def _apply_ten_loai_van_ban(p: ET.Element, font_pair: int):
    pPr = _ensure_pPr(p)
    _remove_direct_pPr_format(pPr)
    _set_pPr_direct(pPr, jc='center', first_line=0,
                    spacing_before=240, spacing_after=120, line=240,
                    keep_next=True)
    _apply_to_all_runs(p, 'Times New Roman', _sz(font_pair, 'ten_loai_van_ban'),
                       bold=True, italic=False, caps=True)


def _apply_trich_yeu(p: ET.Element, font_pair: int):
    pPr = _ensure_pPr(p)
    _remove_direct_pPr_format(pPr)
    _set_pPr_direct(pPr, jc='center', first_line=0,
                    spacing_before=120, spacing_after=240, line=240)
    _apply_to_all_runs(p, 'Times New Roman', _sz(font_pair, 'trich_yeu'),
                       bold=True, italic=False, caps=False)


def _apply_trich_yeu_cong_van(p: ET.Element, font_pair: int):
    pPr = _ensure_pPr(p)
    _remove_direct_pPr_format(pPr)
    _set_pPr_direct(pPr, jc='center', first_line=0,
                    spacing_before=120, spacing_after=0, line=240)
    _apply_to_all_runs(p, 'Times New Roman', _sz(font_pair, 'trich_yeu_cong_van'),
                       bold=False, italic=False, caps=False)


def _apply_kinh_gui(p: ET.Element, font_pair: int):
    pPr = _ensure_pPr(p)
    _remove_direct_pPr_format(pPr)
    _set_pPr_direct(pPr, jc='both', first_line=567,
                    spacing_before=120, spacing_after=0, line=240)
    _apply_to_all_runs(p, 'Times New Roman', _sz(font_pair, 'kinh_gui'),
                       bold=False, italic=False, caps=False)


def _apply_chan_ky_quyen_han(p: ET.Element, font_pair: int):
    pPr = _ensure_pPr(p)
    _remove_direct_pPr_format(pPr)
    _set_pPr_direct(pPr, jc='center', first_line=0,
                    spacing_before=0, spacing_after=0, line=240)
    _apply_to_all_runs(p, 'Times New Roman', _sz(font_pair, 'chan_ky_quyen_han'),
                       bold=True, italic=False, caps=True)


def _apply_chan_ky_chuc_vu(p: ET.Element, font_pair: int):
    pPr = _ensure_pPr(p)
    _remove_direct_pPr_format(pPr)
    _set_pPr_direct(pPr, jc='center', first_line=0,
                    spacing_before=0, spacing_after=0, line=240)
    _apply_to_all_runs(p, 'Times New Roman', _sz(font_pair, 'chan_ky_chuc_vu'),
                       bold=True, italic=False, caps=True)


def _apply_chan_ky_ho_ten(p: ET.Element, font_pair: int):
    pPr = _ensure_pPr(p)
    _remove_direct_pPr_format(pPr)
    # Chân ký họ tên: chừa khoảng cách cho chữ ký (1200 twips ≈ 60pt)
    _set_pPr_direct(pPr, jc='center', first_line=0,
                    spacing_before=1200, spacing_after=0, line=240)
    _apply_to_all_runs(p, 'Times New Roman', _sz(font_pair, 'chan_ky_ho_ten'),
                       bold=True, italic=False, caps=False)


def _apply_phu_luc_label(p: ET.Element, font_pair: int):
    pPr = _ensure_pPr(p)
    _remove_direct_pPr_format(pPr)
    _set_pPr_direct(pPr, jc='center', first_line=0,
                    spacing_before=240, spacing_after=120, line=240,
                    keep_next=True)
    _apply_to_all_runs(p, 'Times New Roman', _sz(font_pair, 'phu_luc_label'),
                       bold=True, italic=False, caps=False)


def _apply_phu_luc_tieu_de(p: ET.Element, font_pair: int):
    pPr = _ensure_pPr(p)
    _remove_direct_pPr_format(pPr)
    _set_pPr_direct(pPr, jc='center', first_line=0,
                    spacing_before=0, spacing_after=120, line=240)
    _apply_to_all_runs(p, 'Times New Roman', _sz(font_pair, 'phu_luc_tieu_de'),
                       bold=True, italic=False, caps=True)


# Map type → function (chỉ cho direct types)
DIRECT_APPLY_FUNCS = {
    'quoc_hieu': _apply_quoc_hieu,
    'tieu_nhu': _apply_tieu_ngu,   # alias phòng nhầm
    'tieu_ngu': _apply_tieu_ngu,
    'ten_co_quan_chu_quan': _apply_ten_co_quan_chu_quan,
    'ten_co_quan_ban_hanh': _apply_ten_co_quan_ban_hanh,
    'so_ky_hieu': _apply_so_ky_hieu,
    'dia_danh_ngay_thang': _apply_dia_danh_ngay_thang,
    'kinh_gui': _apply_kinh_gui,
    'chan_ky_quyen_han': _apply_chan_ky_quyen_han,
    'chan_ky_chuc_vu': _apply_chan_ky_chuc_vu,
    'chan_ky_ho_ten': _apply_chan_ky_ho_ten,
    'phu_luc_label': _apply_phu_luc_label,
    'phu_luc_tieu_de': _apply_phu_luc_tieu_de,
}

# Title với direct override spacing/run per subtype
def _apply_title_with_override(p: ET.Element, comp_type: str, font_pair: int):
    """
    Gán pStyle=Title sau đó áp direct override để phân biệt
    ten_loai_van_ban / trich_yeu / trich_yeu_cong_van.
    """
    pPr = _ensure_pPr(p)
    _set_pStyle(pPr, 'Title')
    _remove_direct_pPr_format(pPr)

    if comp_type == 'ten_loai_van_ban':
        _set_pPr_direct(pPr, jc='center', first_line=0,
                        spacing_before=240, spacing_after=120, line=240,
                        keep_next=True)
        sz = _sz(font_pair, 'ten_loai_van_ban')
        _apply_to_all_runs(p, 'Times New Roman', sz,
                           bold=True, italic=False, caps=True)
    elif comp_type == 'trich_yeu':
        _set_pPr_direct(pPr, jc='center', first_line=0,
                        spacing_before=120, spacing_after=240, line=240)
        sz = _sz(font_pair, 'trich_yeu')
        _apply_to_all_runs(p, 'Times New Roman', sz,
                           bold=True, italic=False, caps=False)
    elif comp_type == 'trich_yeu_cong_van':
        _set_pPr_direct(pPr, jc='center', first_line=0,
                        spacing_before=120, spacing_after=240, line=240)
        sz = _sz(font_pair, 'trich_yeu_cong_van')
        _apply_to_all_runs(p, 'Times New Roman', sz,
                           bold=False, italic=False, caps=False)


TITLE_TYPES = {'ten_loai_van_ban', 'trich_yeu', 'trich_yeu_cong_van'}


def apply_style_based(p: ET.Element, style_id: str, font_pair: int,
                       comp_type: str):
    """
    Áp pStyle: gán <w:pStyle>, xóa direct pPr override,
    chuẩn hóa cỡ chữ runs về đúng cặp.
    """
    pPr = _ensure_pPr(p)
    _set_pStyle(pPr, style_id)
    _remove_direct_pPr_format(pPr)

    if comp_type.startswith('heading_') or comp_type == 'khoan_co_tieu_de':
        sz = _sz(font_pair, 'heading')
    elif comp_type == 'can_cu':
        sz = _sz(font_pair, 'can_cu')
    elif comp_type == 'noi_nhan_label':
        sz = _sz(font_pair, 'noi_nhan_label')
    elif comp_type == 'noi_nhan_item':
        sz = _sz(font_pair, 'noi_nhan_item')
    else:
        sz = _sz(font_pair, 'body')

    _apply_normalize_run_size(p, sz)


def run_phase3(unpacked_dir, classifications: Dict[int, str],
               font_pair: int, heading_type: str, report: Dict,
               level_map: Dict[str, int] = None) -> Dict:
    """
    Entrypoint Phase 3.
    level_map: {entity: effective_heading_level} từ Phase 2.
    """
    if level_map is None:
        level_map = {}

    doc_xml = Path(unpacked_dir) / 'word' / 'document.xml'
    tree = parse_xml(doc_xml)
    root = tree.getroot()
    paragraphs = list(root.iter(f'{W}p'))

    phase_report = {
        'style_based_count': 0,
        'direct_format_count': 0,
        'by_type': {},
    }

    for i, p in enumerate(paragraphs):
        comp_type = classifications.get(i, 'unknown')
        phase_report['by_type'][comp_type] = \
            phase_report['by_type'].get(comp_type, 0) + 1

        if comp_type in TITLE_TYPES:
            _apply_title_with_override(p, comp_type, font_pair)
            phase_report['style_based_count'] += 1

        elif comp_type in DIRECT_TYPES:
            func = DIRECT_APPLY_FUNCS.get(comp_type)
            if func:
                func(p, font_pair)
                phase_report['direct_format_count'] += 1

        elif comp_type in STYLE_TYPES and comp_type not in TITLE_TYPES:
            style_id = _resolve_style_id(comp_type, level_map)
            apply_style_based(p, style_id, font_pair, comp_type)
            phase_report['style_based_count'] += 1

        elif comp_type == 'unknown':
            pass

    write_xml_preserve_root_attrs(
        tree, doc_xml,
        get_original_xml(doc_xml.parent.parent, doc_xml.name)
    )
    report['phase3'] = phase_report
    return report
