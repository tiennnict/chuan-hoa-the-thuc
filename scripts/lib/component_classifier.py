"""
Phase 2: Phân loại từng paragraph thành component_type.

Logic chính:
1. Xác định cấu trúc nội dung: 6a (có Điều) hay 6b (không có Điều).
2. Rà soát heading cấp nào hiện diện để tính effective_level (đẩy heading lên).
3. Gán component_type + lưu effective_heading_level vào metadata.
"""

import re
from typing import Dict, List, Optional, Set, Tuple
from xml.etree import ElementTree as ET
from .xml_utils import parse_xml


NS_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = f"{{{NS_W}}}"


# --- Regex patterns ---
RE_QUOC_HIEU = re.compile(r'CỘNG\s*HO[ÀA]\s+XÃ\s+HỘI\s+CHỦ\s+NGHĨA\s+VIỆT\s+NAM',
                          re.IGNORECASE)
RE_TIEU_NGU = re.compile(r'Độc\s*lập\s*[-–—]\s*Tự\s*do\s*[-–—]\s*Hạnh\s*phúc',
                         re.IGNORECASE)
RE_SO_KY_HIEU = re.compile(r'^\s*Số\s*:\s*\d+', re.IGNORECASE)
RE_DIA_DANH_NGAY = re.compile(
    r',\s*ngày\s+\d{1,2}\s+tháng\s+\d{1,2}\s+năm\s+\d{4}', re.IGNORECASE)
RE_CAN_CU = re.compile(r'^\s*Căn\s+cứ\s+', re.IGNORECASE)
RE_KINH_GUI = re.compile(r'^\s*Kính\s+gửi\s*:', re.IGNORECASE)
RE_NOI_NHAN_LABEL = re.compile(r'^\s*Nơi\s+nhận\s*:', re.IGNORECASE)
RE_PHU_LUC_LABEL = re.compile(r'^\s*Phụ\s+lục\s+[IVX0-9]+\b', re.IGNORECASE)
RE_TRICH_YEU_CV = re.compile(r'^\s*V/v\s+', re.IGNORECASE)
RE_CHAN_KY_QH = re.compile(r'^\s*(TM\.|KT\.|TL\.|TUQ\.|Q\.)\s*', re.UNICODE)

# Heading patterns
RE_PHAN = re.compile(r'^\s*Phần\s+[IVX]+\b', re.IGNORECASE)
RE_CHUONG = re.compile(r'^\s*Chương\s+[IVX]+\b', re.IGNORECASE)
RE_MUC_6A = re.compile(r'^\s*Mục\s+\d+\b', re.IGNORECASE)
RE_TIEU_MUC = re.compile(r'^\s*Tiểu\s*mục\s+\d+\b', re.IGNORECASE)
RE_DIEU = re.compile(r'^\s*Điều\s+\d+\s*\.\s', re.IGNORECASE)
RE_MUC_6B = re.compile(r'^\s*[IVX]+\s*\.\s+[A-ZÀ-Ỹ]', re.UNICODE)

# Khoản có tiêu đề: "N. Tên khoản" — đầu chữ hoa nhưng không toàn hoa (in thường)
RE_KHOAN_CO_TIEU_DE = re.compile(r'^\s*\d+\s*\.\s+[A-ZÀ-Ỹ][a-zà-ỹ]', re.UNICODE)

# Cấu trúc không chuẩn: 1.1, 1.1.1
RE_SUBITEM_NONSTANDARD = re.compile(r'^\s*\d+\s*\.\s*\d+', re.UNICODE)

# Điểm bảng chữ cái tiếng Việt
RE_DIEM_CHU_CAI = re.compile(
    r'^\s*[abcdđeghiklmnoqrstuvxy]\s*\)', re.UNICODE)

CO_QUAN_PREFIXES = ('BỘ ', 'UBND', 'SỞ ', 'CỤC ', 'TỔNG CỤC', 'PHÒNG ',
                    'BAN ', 'VIỆN ', 'TRUNG TÂM', 'ỦY BAN',
                    'HỘI ĐỒNG', 'CHI CỤC', 'VĂN PHÒNG')


def _get_text(p: ET.Element) -> str:
    return ''.join(t.text for t in p.iter(f'{W}t') if t.text).strip()


def _get_jc(p: ET.Element) -> str:
    pPr = p.find(f'{W}pPr')
    if pPr is None:
        return 'left'
    jc = pPr.find(f'{W}jc')
    return jc.get(f'{W}val', 'left') if jc is not None else 'left'


def _is_bold(p: ET.Element) -> bool:
    for b in p.iter(f'{W}b'):
        if b.get(f'{W}val', '1') not in ('0', 'false'):
            return True
    return False


def _is_all_upper(text: str) -> bool:
    letters = [c for c in text if c.isalpha()]
    return bool(letters) and all(c.isupper() for c in letters)


def detect_structure(paragraphs: List[ET.Element]) -> str:
    for p in paragraphs:
        if RE_DIEU.match(_get_text(p)):
            return '6a'
    return '6b'


def compute_heading_level_map(
    paragraphs: List[ET.Element],
    structure: str
) -> Dict[str, int]:
    present: Set[str] = set()
    for p in paragraphs:
        text = _get_text(p)
        if RE_PHAN.match(text):
            present.add('phan')
        if structure == '6a':
            if RE_CHUONG.match(text):
                present.add('chuong')
            if RE_MUC_6A.match(text):
                present.add('muc')
            if RE_TIEU_MUC.match(text):
                present.add('tieu_muc')
            if RE_DIEU.match(text):
                present.add('dieu')
        else:
            if RE_MUC_6B.match(text):
                present.add('muc_6b')
            if RE_KHOAN_CO_TIEU_DE.match(text):
                present.add('khoan_co_tieu_de')

    level_map: Dict[str, int] = {}
    if structure == '6a':
        seq = ['phan', 'chuong', 'muc', 'tieu_muc', 'dieu']
    else:
        seq = ['phan', 'muc_6b', 'khoan_co_tieu_de']

    lvl = 1
    for entity in seq:
        if entity in present:
            level_map[entity] = lvl
            lvl += 1
    return level_map


def classify_quoc_hieu_table(root, classifications, para_index):
    for tbl in root.iter(f'{W}tbl'):
        joined = ' '.join(t.text for t in tbl.iter(f'{W}t') if t.text)
        if not RE_QUOC_HIEU.search(joined):
            continue
        for tc in tbl.iter(f'{W}tc'):
            cps = list(tc.iter(f'{W}p'))
            ct = ' '.join(_get_text(p) for p in cps)
            if RE_QUOC_HIEU.search(ct):
                qh, tn = False, False
                for p in cps:
                    t = _get_text(p)
                    idx = para_index[p]
                    if not qh and RE_QUOC_HIEU.search(t):
                        classifications[idx] = 'quoc_hieu'; qh = True
                    elif not tn and RE_TIEU_NGU.search(t):
                        classifications[idx] = 'tieu_ngu'; tn = True
            else:
                ne = [p for p in cps if _get_text(p)]
                if not ne:
                    continue
                if len(ne) == 1:
                    classifications[para_index[ne[0]]] = 'ten_co_quan_ban_hanh'
                else:
                    for p in ne[:-1]:
                        classifications[para_index[p]] = 'ten_co_quan_chu_quan'
                    classifications[para_index[ne[-1]]] = 'ten_co_quan_ban_hanh'
        return


def classify_so_kyhieu_table(root, classifications, para_index):
    for tbl in root.iter(f'{W}tbl'):
        joined = ' '.join(t.text for t in tbl.iter(f'{W}t') if t.text)
        if not (re.search(r'Số\s*:\s*\d', joined) or RE_DIA_DANH_NGAY.search(joined)):
            continue
        for tc in tbl.iter(f'{W}tc'):
            for p in tc.iter(f'{W}p'):
                text = _get_text(p)
                idx = para_index[p]
                if idx in classifications or not text:
                    continue
                if RE_SO_KY_HIEU.match(text):
                    classifications[idx] = 'so_ky_hieu'
                elif RE_DIA_DANH_NGAY.search(text):
                    classifications[idx] = 'dia_danh_ngay_thang'


def classify_noi_nhan_table(root, classifications, para_index):
    found_tbl = None
    for tbl in root.iter(f'{W}tbl'):
        joined = ' '.join(t.text for t in tbl.iter(f'{W}t') if t.text)
        if RE_NOI_NHAN_LABEL.search(joined):
            found_tbl = tbl
    if found_tbl is None:
        return
    for tc in found_tbl.iter(f'{W}tc'):
        cps = list(tc.iter(f'{W}p'))
        ct = ' '.join(_get_text(p) for p in cps)
        if RE_NOI_NHAN_LABEL.search(ct):
            for p in cps:
                t = _get_text(p)
                idx = para_index[p]
                if RE_NOI_NHAN_LABEL.match(t):
                    classifications[idx] = 'noi_nhan_label'
                elif t:
                    classifications[idx] = 'noi_nhan_item'
        else:
            ne = [p for p in cps if _get_text(p)]
            if not ne:
                continue
            start = 0
            if RE_CHAN_KY_QH.match(_get_text(ne[0])):
                classifications[para_index[ne[0]]] = 'chan_ky_quyen_han'
                start = 1
            rem = ne[start:]
            ho_ten_idx = None
            for j in range(len(rem) - 1, -1, -1):
                t = _get_text(rem[j])
                if t and not _is_all_upper(t):
                    ho_ten_idx = j
                    break
            for j, p in enumerate(rem):
                t = _get_text(p)
                if not t:
                    continue
                classifications[para_index[p]] = (
                    'chan_ky_ho_ten' if j == ho_ten_idx else 'chan_ky_chuc_vu'
                )


def classify_quoc_hieu_fallback(paragraphs, classifications, para_index):
    if 'quoc_hieu' in classifications.values():
        return
    for p in paragraphs[:30]:
        idx = para_index[p]
        if idx in classifications:
            continue
        text = _get_text(p)
        if not text:
            continue
        if RE_QUOC_HIEU.search(text) and _get_jc(p) == 'center':
            classifications[idx] = 'quoc_hieu'
        elif RE_TIEU_NGU.search(text) and _get_jc(p) == 'center':
            classifications[idx] = 'tieu_ngu'
    if 'ten_co_quan_ban_hanh' in classifications.values():
        return
    candidates = []
    for p in paragraphs[:30]:
        idx = para_index[p]
        if idx in classifications:
            continue
        text = _get_text(p)
        if not text or not _is_all_upper(text) or _get_jc(p) != 'center':
            continue
        if any(text.startswith(pf) for pf in CO_QUAN_PREFIXES):
            candidates.append(idx)
    if candidates:
        bold = [idx for idx in candidates if _is_bold(paragraphs[idx])]
        if bold:
            classifications[bold[-1]] = 'ten_co_quan_ban_hanh'
            for idx in candidates:
                if idx != bold[-1] and idx not in classifications:
                    classifications[idx] = 'ten_co_quan_chu_quan'
        else:
            classifications[candidates[-1]] = 'ten_co_quan_ban_hanh'
            for idx in candidates[:-1]:
                classifications[idx] = 'ten_co_quan_chu_quan'


def classify_ten_loai_trich_yeu(paragraphs, classifications, para_index, doc_type):
    for i, p in enumerate(paragraphs):
        idx = para_index[p]
        if idx in classifications:
            continue
        text = _get_text(p)
        if not text:
            continue
        if RE_TRICH_YEU_CV.match(text):
            classifications[idx] = 'trich_yeu_cong_van'
            continue
        if doc_type != 'Công văn':
            if (
                _is_all_upper(text)
                and _get_jc(p) == 'center'
                and 3 <= len(text) <= 80
                and not RE_QUOC_HIEU.search(text)
                and not any(text.startswith(pf) for pf in CO_QUAN_PREFIXES)
                and 'ten_loai_van_ban' not in classifications.values()
            ):
                classifications[idx] = 'ten_loai_van_ban'
                for j in range(i + 1, min(i + 4, len(paragraphs))):
                    np_ = paragraphs[j]
                    nidx = para_index[np_]
                    if nidx in classifications:
                        continue
                    nt = _get_text(np_)
                    if not nt:
                        continue
                    if _get_jc(np_) == 'center':
                        classifications[nidx] = 'trich_yeu'
                    break


def classify_headings_body(
    paragraphs, classifications, para_index,
    structure, level_map, nonstandard_flags
):
    for p in paragraphs:
        idx = para_index[p]
        if idx in classifications:
            continue
        text = _get_text(p)
        if not text:
            classifications[idx] = 'body'
            continue

        if RE_PHU_LUC_LABEL.match(text):
            classifications[idx] = 'phu_luc_label'
            continue
        if RE_CAN_CU.match(text):
            classifications[idx] = 'can_cu'
            continue
        if RE_KINH_GUI.match(text):
            classifications[idx] = 'kinh_gui'
            continue

        # Cấu trúc không chuẩn 1.1.x
        if RE_SUBITEM_NONSTANDARD.match(text):
            classifications[idx] = 'body'
            nonstandard_flags.append({
                'paragraph_index': idx,
                'excerpt': text[:80],
                'message': (
                    'Cấu trúc số thứ tự "1.1.x" không đúng chuẩn '
                    'Nghị định số 30/2020/NĐ-CP. Đề nghị rà soát và chuyển sang '
                    'cấu trúc Điều/Khoản/Điểm theo quy định.'
                )
            })
            continue

        # Headings
        if RE_PHAN.match(text) and 'phan' in level_map:
            classifications[idx] = 'heading_phan'
            continue

        if structure == '6a':
            if RE_CHUONG.match(text) and 'chuong' in level_map:
                classifications[idx] = 'heading_chuong'
                continue
            if RE_MUC_6A.match(text) and 'muc' in level_map:
                classifications[idx] = 'heading_muc'
                continue
            if RE_TIEU_MUC.match(text) and 'tieu_muc' in level_map:
                classifications[idx] = 'heading_tieu_muc'
                continue
            if RE_DIEU.match(text) and 'dieu' in level_map:
                classifications[idx] = 'heading_dieu'
                continue
        else:  # 6b
            if RE_MUC_6B.match(text) and 'muc_6b' in level_map:
                classifications[idx] = 'heading_muc'
                continue
            if RE_KHOAN_CO_TIEU_DE.match(text):
                classifications[idx] = 'khoan_co_tieu_de'
                continue

        classifications[idx] = 'body'


def classify_all(
    unpacked_dir,
    doc_type: str,
    heading_type: str   # kept for backward compat
):
    """
    Entrypoint Phase 2.
    Trả về (classifications, level_map, structure, nonstandard_flags).
    """
    from pathlib import Path
    doc_xml = Path(unpacked_dir) / 'word' / 'document.xml'
    tree = parse_xml(doc_xml)
    root = tree.getroot()
    paragraphs = list(root.iter(f'{W}p'))
    para_index = {p: i for i, p in enumerate(paragraphs)}
    classifications: Dict[int, str] = {}
    nonstandard_flags: List[Dict] = []

    structure = detect_structure(paragraphs)
    level_map = compute_heading_level_map(paragraphs, structure)

    classify_quoc_hieu_table(root, classifications, para_index)
    classify_so_kyhieu_table(root, classifications, para_index)
    classify_noi_nhan_table(root, classifications, para_index)

    for p in paragraphs:
        idx = para_index[p]
        if idx in classifications:
            continue
        text = _get_text(p)
        if not text:
            continue
        if RE_SO_KY_HIEU.match(text):
            classifications[idx] = 'so_ky_hieu'
        elif RE_DIA_DANH_NGAY.search(text) and _get_jc(p) == 'center':
            classifications[idx] = 'dia_danh_ngay_thang'

    classify_quoc_hieu_fallback(paragraphs, classifications, para_index)
    classify_ten_loai_trich_yeu(paragraphs, classifications, para_index, doc_type)
    classify_headings_body(
        paragraphs, classifications, para_index,
        structure, level_map, nonstandard_flags
    )

    for p in paragraphs:
        idx = para_index[p]
        if idx not in classifications:
            classifications[idx] = 'body'

    return classifications, level_map, structure, nonstandard_flags
