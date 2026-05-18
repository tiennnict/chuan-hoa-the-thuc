"""
Phase 3 (phần bảng): chuẩn hóa định dạng bảng trong document.xml.

Phân loại bảng:
- special_quoc_hieu  : bảng Quốc hiệu + Tên cơ quan (đầu văn bản)
- special_noi_nhan   : bảng Nơi nhận + Chân ký (cuối văn bản)
- special_kinh_gui   : bảng Kính gửi (Công văn nhiều nơi nhận)
- regular            : mọi bảng còn lại

Quy tắc áp dụng:

Cấp bảng (tblPr) — chỉ áp cho regular:
  - tblInd  w=0 type=dxa
  - jc      center
  - tblW    w=0 type=pct  +  tblLayout type=autofit

Cấp cell (tcPr) — áp cho mọi loại bảng:
  - special_quoc_hieu / special_noi_nhan : vAlign=top
  - special_kinh_gui                     : vAlign=top
  - regular                              : vAlign=center

Cấp paragraph (pPr) trong cell — áp cho mọi loại bảng:
  - firstLine=0 (luôn)
  - special_quoc_hieu / special_noi_nhan : jc=center
  - special_kinh_gui                     : jc=left (giữ nguyên)
  - regular                              : xem quy tắc Header / body bên dưới

Bảng regular — Header detection:
  - Ô [row=0, col=0] sau khi bỏ qua rowspan/colspan chứa text "STT" hoặc "TT"
    (so sánh không phân biệt hoa thường, bỏ dấu cách)
  - Nếu đúng: xác định header_row_count = rowspan của ô đó (mặc định 1)
  - Tất cả hàng trong phạm vi header_row_count:
      * jc=center, bold=true, keepNext, vAlign=center
      * Áp tblHeader trên trPr của mỗi hàng (Repeat Header Rows)
  - Cột đầu tiên (col=0) của mọi hàng (kể cả body): jc=center
  - Body cells (ngoài header): jc giữ nguyên gốc (chỉ sửa vAlign)
  - Nếu ô [0,0] không phải STT/TT: giữ nguyên jc mọi cell, chỉ sửa vAlign=center
"""

import re
from typing import List, Optional, Set, Tuple
from xml.etree import ElementTree as ET

NS_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = f"{{{NS_W}}}"

RE_QUOC_HIEU = re.compile(
    r'CỘNG\s*HO[ÀA]\s+XÃ\s+HỘI\s+CHỦ\s+NGHĨA\s+VIỆT\s+NAM', re.IGNORECASE)
RE_NOI_NHAN = re.compile(r'Nơi\s+nhận\s*:', re.IGNORECASE)
RE_KINH_GUI_CELL = re.compile(r'^\s*Kính\s+gửi\s*:', re.IGNORECASE)
RE_STT = re.compile(r'^\s*(STT|TT)\s*$', re.IGNORECASE)


# ---------------------------------------------------------------------------
# Helpers XML
# ---------------------------------------------------------------------------

def _text(el: ET.Element) -> str:
    """Lấy toàn bộ text từ một element (bất kể cấp)."""
    return ''.join(t.text for t in el.iter(f'{W}t') if t.text)


def _ensure(parent: ET.Element, tag: str, insert_first: bool = False) -> ET.Element:
    """Lấy child tag, tạo mới nếu chưa có."""
    child = parent.find(tag)
    if child is None:
        child = ET.SubElement(parent, tag)
        if insert_first:
            parent.remove(child)
            parent.insert(0, child)
    return child


def _remove_all(parent: ET.Element, tag: str):
    for el in parent.findall(tag):
        parent.remove(el)


def _set_attr(el: ET.Element, attr: str, val: str):
    el.set(f'{W}{attr}', val)


# ---------------------------------------------------------------------------
# Nhận diện loại bảng
# ---------------------------------------------------------------------------

def _classify_table(tbl: ET.Element) -> str:
    """Trả về 'special_quoc_hieu', 'special_noi_nhan', 'special_kinh_gui', hoặc 'regular'."""
    joined = _text(tbl)

    if RE_QUOC_HIEU.search(joined):
        return 'special_quoc_hieu'
    if RE_NOI_NHAN.search(joined):
        return 'special_noi_nhan'

    # Bảng Kính gửi: ô đầu tiên của bảng chứa "Kính gửi:"
    rows = tbl.findall(f'{W}tr')
    if rows:
        first_row_cells = rows[0].findall(f'{W}tc')
        if first_row_cells:
            first_cell_text = _text(first_row_cells[0])
            if RE_KINH_GUI_CELL.match(first_cell_text):
                return 'special_kinh_gui'

    return 'regular'


# ---------------------------------------------------------------------------
# Cấp bảng (tblPr)
# ---------------------------------------------------------------------------

def _apply_tbl_pr_regular(tbl: ET.Element):
    """Áp tblPr cho bảng regular: jc=center, tblInd=0, Autofit Windows."""
    tblPr = _ensure(tbl, f'{W}tblPr', insert_first=True)

    # tblInd w=0 dxa
    _remove_all(tblPr, f'{W}tblInd')
    tblInd = ET.SubElement(tblPr, f'{W}tblInd')
    _set_attr(tblInd, 'w', '0')
    _set_attr(tblInd, 'type', 'dxa')

    # jc center
    _remove_all(tblPr, f'{W}jc')
    jc_el = ET.SubElement(tblPr, f'{W}jc')
    _set_attr(jc_el, 'val', 'center')

    # tblW pct=0 (Autofit Windows)
    _remove_all(tblPr, f'{W}tblW')
    tblW = ET.SubElement(tblPr, f'{W}tblW')
    _set_attr(tblW, 'w', '0')
    _set_attr(tblW, 'type', 'pct')

    # tblLayout autofit
    _remove_all(tblPr, f'{W}tblLayout')
    tblLayout = ET.SubElement(tblPr, f'{W}tblLayout')
    _set_attr(tblLayout, 'type', 'autofit')


# ---------------------------------------------------------------------------
# Cấp cell (tcPr) — vAlign
# ---------------------------------------------------------------------------

def _set_cell_valign(tc: ET.Element, valign: str):
    """Set <w:vAlign w:val="..."/> trong tcPr."""
    tcPr = _ensure(tc, f'{W}tcPr', insert_first=True)
    _remove_all(tcPr, f'{W}vAlign')
    vAlign_el = ET.SubElement(tcPr, f'{W}vAlign')
    _set_attr(vAlign_el, 'val', valign)


# ---------------------------------------------------------------------------
# Cấp paragraph (pPr) trong cell
# ---------------------------------------------------------------------------

def _set_para_firstline_zero(p: ET.Element):
    """Xóa firstLine / hanging indent, đảm bảo ind firstLine=0."""
    pPr = _ensure(p, f'{W}pPr')
    # Xóa ind cũ
    _remove_all(pPr, f'{W}ind')
    ind = ET.SubElement(pPr, f'{W}ind')
    _set_attr(ind, 'firstLine', '0')


def _set_para_jc(p: ET.Element, jc: str):
    pPr = _ensure(p, f'{W}pPr')
    _remove_all(pPr, f'{W}jc')
    jc_el = ET.SubElement(pPr, f'{W}jc')
    _set_attr(jc_el, 'val', jc)


def _set_para_keep_next(p: ET.Element):
    pPr = _ensure(p, f'{W}pPr')
    if pPr.find(f'{W}keepNext') is None:
        # keepNext nên đứng trước spacing/ind/jc
        _remove_all(pPr, f'{W}keepNext')
        # Insert sau pStyle (index 0 nếu không có pStyle, sau pStyle nếu có)
        pStyle = pPr.find(f'{W}pStyle')
        pos = 1 if pStyle is not None else 0
        kn = ET.Element(f'{W}keepNext')
        pPr.insert(pos, kn)


def _set_run_bold(p: ET.Element, bold: bool):
    """Set bold trên tất cả run trong paragraph."""
    for r in p.findall(f'{W}r'):
        rPr = _ensure(r, f'{W}rPr', insert_first=True)
        _remove_all(rPr, f'{W}b')
        _remove_all(rPr, f'{W}bCs')
        if bold:
            ET.SubElement(rPr, f'{W}b')
            ET.SubElement(rPr, f'{W}bCs')


# ---------------------------------------------------------------------------
# Header detection cho bảng regular
# ---------------------------------------------------------------------------

def _get_cell_rowspan(tc: ET.Element) -> int:
    """Lấy gridSpan theo chiều dọc (vMerge restart = bắt đầu merge)."""
    # rowspan được encode bằng vMerge: ô đầu có vMerge val=restart hoặc không có val,
    # các ô tiếp theo có vMerge không có val (continuation).
    # Để tính header_row_count ta cần đếm từ ngoài (xem _find_header_row_count).
    tcPr = tc.find(f'{W}tcPr')
    if tcPr is None:
        return 1
    vMerge = tcPr.find(f'{W}vMerge')
    if vMerge is None:
        return 1
    val = vMerge.get(f'{W}val', '')
    # val='restart' hoặc val='' (không có attr) đều là bắt đầu merge
    return 1  # actual span tính bên ngoài


def _find_header_row_count(rows: List[ET.Element]) -> int:
    """
    Đếm số hàng header dựa trên vMerge của ô [0,0].
    - Nếu ô [0,0] không có vMerge: header_row_count = 1
    - Nếu có vMerge restart: đếm các hàng tiếp theo có ô cùng cột là vMerge continuation
    """
    if not rows:
        return 1
    first_row_cells = rows[0].findall(f'{W}tc')
    if not first_row_cells:
        return 1

    tc0 = first_row_cells[0]
    tcPr0 = tc0.find(f'{W}tcPr')
    if tcPr0 is None:
        return 1
    vMerge0 = tcPr0.find(f'{W}vMerge')
    if vMerge0 is None:
        return 1

    # Có vMerge: đếm span
    count = 1
    for row in rows[1:]:
        cells = row.findall(f'{W}tc')
        if not cells:
            break
        tcPr = cells[0].find(f'{W}tcPr')
        if tcPr is None:
            break
        vMerge = tcPr.find(f'{W}vMerge')
        if vMerge is None:
            break
        # Continuation: vMerge không có val hoặc val khác 'restart'
        val = vMerge.get(f'{W}val', '')
        if val == 'restart':
            break
        count += 1
    return count


def _is_stt_table(rows: List[ET.Element]) -> bool:
    """Kiểm tra ô [0,0] có phải STT / TT không."""
    if not rows:
        return False
    first_cells = rows[0].findall(f'{W}tc')
    if not first_cells:
        return False
    cell_text = _text(first_cells[0]).strip()
    return bool(RE_STT.match(cell_text))


# ---------------------------------------------------------------------------
# Áp format cho từng loại bảng
# ---------------------------------------------------------------------------

def _apply_special_table(tbl: ET.Element, valign: str, jc: Optional[str]):
    """
    Áp format cho bảng đặc biệt (quốc hiệu, nơi nhận, kính gửi).
    valign: 'top' cho quoc_hieu/noi_nhan/kinh_gui
    jc: 'center' cho quoc_hieu/noi_nhan, None (giữ nguyên) cho kinh_gui
    """
    for tc in tbl.iter(f'{W}tc'):
        _set_cell_valign(tc, valign)
        for p in tc.findall(f'{W}p'):
            _set_para_firstline_zero(p)
            if jc is not None:
                _set_para_jc(p, jc)


def _apply_regular_table(tbl: ET.Element):
    """Áp format cho bảng regular."""
    # 1. tblPr
    _apply_tbl_pr_regular(tbl)

    rows = tbl.findall(f'{W}tr')
    is_stt = _is_stt_table(rows)

    if is_stt:
        header_row_count = _find_header_row_count(rows)
    else:
        header_row_count = 0

    for row_idx, tr in enumerate(rows):
        is_header_row = is_stt and (row_idx < header_row_count)

        # Áp tblHeader cho header rows
        if is_header_row:
            trPr = _ensure(tr, f'{W}trPr', insert_first=True)
            if trPr.find(f'{W}tblHeader') is None:
                ET.SubElement(trPr, f'{W}tblHeader')

        cells = tr.findall(f'{W}tc')
        for col_idx, tc in enumerate(cells):
            # vAlign: luôn center cho bảng regular
            _set_cell_valign(tc, 'center')

            for p in tc.findall(f'{W}p'):
                # firstLine=0 luôn
                _set_para_firstline_zero(p)

                if is_header_row:
                    # Header: jc=center, bold, keepNext
                    _set_para_jc(p, 'center')
                    _set_run_bold(p, bold=True)
                    _set_para_keep_next(p)
                else:
                    if is_stt and col_idx == 0:
                        # Cột STT/TT body: jc=center
                        _set_para_jc(p, 'center')
                    # else: giữ nguyên jc gốc


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def run_table_format(root: ET.Element, report: dict) -> dict:
    """
    Duyệt tất cả <w:tbl> trong document root, phân loại và áp format.
    Gọi sau khi Phase 3 paragraph đã xong.
    Trả về report đã bổ sung mục 'table_format'.
    """
    table_report = {
        'special_quoc_hieu': 0,
        'special_noi_nhan': 0,
        'special_kinh_gui': 0,
        'regular_stt': 0,
        'regular_plain': 0,
    }

    for tbl in root.iter(f'{W}tbl'):
        kind = _classify_table(tbl)

        if kind == 'special_quoc_hieu':
            _apply_special_table(tbl, valign='top', jc='center')
            table_report['special_quoc_hieu'] += 1

        elif kind == 'special_noi_nhan':
            _apply_special_table(tbl, valign='top', jc='center')
            table_report['special_noi_nhan'] += 1

        elif kind == 'special_kinh_gui':
            _apply_special_table(tbl, valign='top', jc=None)
            table_report['special_kinh_gui'] += 1

        else:  # regular
            is_stt = _is_stt_table(tbl.findall(f'{W}tr'))
            _apply_regular_table(tbl)
            if is_stt:
                table_report['regular_stt'] += 1
            else:
                table_report['regular_plain'] += 1

    report.setdefault('phase3', {})['table_format'] = table_report
    return report
