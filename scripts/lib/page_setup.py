"""
Phase 4: Page Setup (page size + margins) cho mọi section, portrait + landscape.
Phase 5: Header (số trang) cho mọi section.

Quy tắc page setup (clamp về biên gần nhất):
- top: 20-25 mm  (1134-1418 twips)
- bottom: 20-25 mm  (1134-1418 twips)
- left: 30-35 mm  (1701-1985 twips)
- right: 15-20 mm  (851-1134 twips)
"""

from xml.etree import ElementTree as ET
from .xml_utils import parse_xml, write_xml_preserve_root_attrs, get_original_xml
from pathlib import Path
from typing import Dict


NS_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
W = f"{{{NS_W}}}"
R = f"{{{NS_R}}}"

# Constants (twips)
A4_W = 11906
A4_H = 16838
MARGIN_BOUNDS = {
    'top': (1134, 1418),     # 20-25 mm
    'bottom': (1134, 1418),  # 20-25 mm
    'left': (1701, 1985),    # 30-35 mm
    'right': (851, 1134),    # 15-20 mm
}


def _clamp(value: int, low: int, high: int) -> int:
    """Clamp value vào [low, high]. Trong range → giữ; ngoài → kéo về biên gần nhất."""
    if value < low:
        return low
    if value > high:
        return high
    return value


def _ensure_int(s: str, default: int) -> int:
    try:
        return int(s)
    except (ValueError, TypeError):
        return default


def _process_section(sectPr: ET.Element, report_entry: Dict):
    """Chuẩn hóa 1 section: page size + margins."""
    # Detect orientation
    pgSz = sectPr.find(f'{W}pgSz')
    if pgSz is None:
        pgSz = ET.SubElement(sectPr, f'{W}pgSz')

    orient = pgSz.get(f'{W}orient', 'portrait')
    is_landscape = (orient == 'landscape')

    # Set A4 size
    if is_landscape:
        pgSz.set(f'{W}w', str(A4_H))
        pgSz.set(f'{W}h', str(A4_W))
        pgSz.set(f'{W}orient', 'landscape')
    else:
        pgSz.set(f'{W}w', str(A4_W))
        pgSz.set(f'{W}h', str(A4_H))
        if f'{W}orient' in pgSz.attrib:
            del pgSz.attrib[f'{W}orient']

    report_entry['orientation'] = 'landscape' if is_landscape else 'portrait'

    # Margins
    pgMar = sectPr.find(f'{W}pgMar')
    if pgMar is None:
        pgMar = ET.SubElement(sectPr, f'{W}pgMar')

    # Đọc giá trị hiện tại
    before = {}
    after = {}
    for key in ('top', 'bottom', 'left', 'right'):
        orig = _ensure_int(pgMar.get(f'{W}{key}'), -1)
        before[key] = orig
        low, high = MARGIN_BOUNDS[key]
        # Nếu giá trị không hợp lệ → đặt về low
        if orig < 0:
            new_val = low
        else:
            new_val = _clamp(orig, low, high)
        pgMar.set(f'{W}{key}', str(new_val))
        after[key] = new_val

    # Giữ các thuộc tính khác (header, footer, gutter) — không đụng
    # Mặc định header/footer nếu chưa có
    if not pgMar.get(f'{W}header'):
        pgMar.set(f'{W}header', '567')
    if not pgMar.get(f'{W}footer'):
        pgMar.set(f'{W}footer', '567')
    if not pgMar.get(f'{W}gutter'):
        pgMar.set(f'{W}gutter', '0')

    report_entry['margins_before'] = before
    report_entry['margins_after'] = after


def run_phase4(unpacked_dir, report: Dict) -> Dict:
    """Phase 4: chuẩn hóa page setup cho mọi section."""
    doc_xml = Path(unpacked_dir) / 'word' / 'document.xml'
    tree = parse_xml(doc_xml)
    root = tree.getroot()

    sections_report = []

    # sectPr nằm trong body, có thể là <w:sectPr> con của <w:body> (section cuối)
    # hoặc <w:sectPr> trong <w:pPr> (section khác)
    body = root.find(f'{W}body')
    if body is None:
        return report

    # Section cuối (nằm trực tiếp trong body)
    final_sectPr = body.find(f'{W}sectPr')
    # Sections khác (nằm trong pPr của các paragraph)
    other_sectPrs = [el for el in body.iter(f'{W}sectPr') if el is not final_sectPr]

    all_sectPrs = other_sectPrs + ([final_sectPr] if final_sectPr is not None else [])

    for i, sect in enumerate(all_sectPrs):
        entry = {'index': i}
        _process_section(sect, entry)
        sections_report.append(entry)

    write_xml_preserve_root_attrs(tree, doc_xml, get_original_xml(doc_xml.parent.parent, doc_xml.name))

    report['phase4'] = {'sections': sections_report, 'total_sections': len(all_sectPrs)}
    return report


# ============================================================
# PHASE 5: Header (số trang)
# ============================================================

HEADER_FILENAME = 'header_nd30.xml'
HEADER_REL_ID = 'rIdHeaderND30'

CONTENT_TYPE_HEADER = (
    'application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml'
)
RELATIONSHIP_TYPE_HEADER = (
    'http://schemas.openxmlformats.org/officeDocument/2006/relationships/header'
)


def _build_header_xml(font_pair: int) -> str:
    """Build XML cho file header chứa số trang."""
    sz = 28 if font_pair == 14 else 26
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:hdr xmlns:w="{NS_W}" xmlns:r="{NS_R}">
  <w:p>
    <w:pPr>
      <w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/>
      <w:ind w:firstLine="0"/>
      <w:jc w:val="center"/>
    </w:pPr>
    <w:r>
      <w:rPr>
        <w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>
        <w:sz w:val="{sz}"/>
        <w:szCs w:val="{sz}"/>
      </w:rPr>
      <w:fldChar w:fldCharType="begin"/>
    </w:r>
    <w:r>
      <w:rPr>
        <w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>
        <w:sz w:val="{sz}"/>
        <w:szCs w:val="{sz}"/>
      </w:rPr>
      <w:instrText xml:space="preserve">PAGE</w:instrText>
    </w:r>
    <w:r>
      <w:rPr>
        <w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>
        <w:sz w:val="{sz}"/>
        <w:szCs w:val="{sz}"/>
      </w:rPr>
      <w:fldChar w:fldCharType="end"/>
    </w:r>
  </w:p>
</w:hdr>'''


def _add_to_content_types(unpacked_dir: Path):
    """Thêm <Override> cho header trong [Content_Types].xml."""
    ct_path = unpacked_dir / '[Content_Types].xml'
    if not ct_path.exists():
        return

    content = ct_path.read_text(encoding='utf-8')
    override_xml = (f'<Override PartName="/word/{HEADER_FILENAME}" '
                    f'ContentType="{CONTENT_TYPE_HEADER}"/>')

    if HEADER_FILENAME in content:
        return  # đã có

    # Insert trước </Types>
    content = content.replace('</Types>', f'  {override_xml}\n</Types>')
    ct_path.write_text(content, encoding='utf-8')


def _add_to_document_rels(unpacked_dir: Path):
    """Thêm <Relationship> trong word/_rels/document.xml.rels."""
    rels_path = unpacked_dir / 'word' / '_rels' / 'document.xml.rels'
    if not rels_path.exists():
        return

    content = rels_path.read_text(encoding='utf-8')
    rel_xml = (f'<Relationship Id="{HEADER_REL_ID}" '
               f'Type="{RELATIONSHIP_TYPE_HEADER}" '
               f'Target="{HEADER_FILENAME}"/>')

    if HEADER_REL_ID in content:
        return

    content = content.replace('</Relationships>',
                              f'  {rel_xml}\n</Relationships>')
    rels_path.write_text(content, encoding='utf-8')


def _attach_header_to_sections(unpacked_dir: Path) -> int:
    """
    Gắn <w:headerReference> vào mọi <w:sectPr>, đồng thời:
    - Thêm <w:titlePg/> cho section đầu tiên.
    - Đảm bảo <w:pgNumType w:start="1"/> cho section đầu tiên (đánh số từ 1).
    Trả về số section đã xử lý.
    """
    doc_xml = unpacked_dir / 'word' / 'document.xml'
    tree = parse_xml(doc_xml)
    root = tree.getroot()
    body = root.find(f'{W}body')
    if body is None:
        return 0

    # Lấy tất cả sectPr (theo thứ tự xuất hiện)
    sectPrs = list(body.iter(f'{W}sectPr'))
    count = 0

    for i, sectPr in enumerate(sectPrs):
        # Xóa headerReference cũ với same type (nếu có)
        for hr in sectPr.findall(f'{W}headerReference'):
            sectPr.remove(hr)

        # headerReference phải đặt đầu sectPr theo schema
        hr = ET.Element(f'{W}headerReference')
        hr.set(f'{W}type', 'default')
        hr.set(f'{R}id', HEADER_REL_ID)
        sectPr.insert(0, hr)

        if i == 0:
            # Section đầu tiên: ẩn header trang đầu, đánh số từ 1
            # OOXML schema yêu cầu thứ tự nhất định trong sectPr:
            # headerReference, footerReference, footnotePr, endnotePr, type,
            # pgSz, pgMar, paperSrc, pgBorders, lnNumType, pgNumType, cols,
            # formProt, vAlign, noEndnote, titlePg, textDirection, ...

            # pgNumType phải đặt sau pgMar, trước titlePg
            for old in sectPr.findall(f'{W}pgNumType'):
                sectPr.remove(old)
            pgNumType = ET.Element(f'{W}pgNumType')
            pgNumType.set(f'{W}start', '1')
            pgNumType.set(f'{W}fmt', 'decimal')
            # Tìm vị trí sau pgMar
            children = list(sectPr)
            insert_idx = len(children)
            for j, child in enumerate(children):
                if child.tag in (f'{W}cols', f'{W}formProt', f'{W}vAlign',
                                  f'{W}noEndnote', f'{W}titlePg',
                                  f'{W}textDirection'):
                    insert_idx = j
                    break
            sectPr.insert(insert_idx, pgNumType)

            # titlePg: đặt cuối nhưng trước docGrid, textDirection
            for old in sectPr.findall(f'{W}titlePg'):
                sectPr.remove(old)
            titlePg = ET.Element(f'{W}titlePg')
            children = list(sectPr)
            insert_idx = len(children)
            for j, child in enumerate(children):
                if child.tag in (f'{W}textDirection', f'{W}bidi',
                                  f'{W}rtlGutter', f'{W}docGrid',
                                  f'{W}printerSettings'):
                    insert_idx = j
                    break
            sectPr.insert(insert_idx, titlePg)

        count += 1

    write_xml_preserve_root_attrs(tree, doc_xml, get_original_xml(doc_xml.parent.parent, doc_xml.name))
    return count


def run_phase5(unpacked_dir, font_pair: int, report: Dict) -> Dict:
    """Phase 5: thêm header số trang cho mọi section."""
    unpacked_dir = Path(unpacked_dir)

    # 1. Tạo file header
    header_path = unpacked_dir / 'word' / HEADER_FILENAME
    header_path.parent.mkdir(parents=True, exist_ok=True)
    header_path.write_text(_build_header_xml(font_pair), encoding='utf-8')

    # 2. Thêm vào [Content_Types].xml
    _add_to_content_types(unpacked_dir)

    # 3. Thêm relationship
    _add_to_document_rels(unpacked_dir)

    # 4. Gắn vào sections
    count = _attach_header_to_sections(unpacked_dir)

    report['phase5'] = {
        'sections_with_header': count,
        'header_filename': HEADER_FILENAME,
        'font_pair': font_pair,
    }
    return report
