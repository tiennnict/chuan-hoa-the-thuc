"""
Phase 3 (phần Styles): chuẩn hóa styles.xml.

Quy tắc:
- Cập nhật/thêm các style: Normal, Heading1-Heading5, KhoanCoTieuDe, CanCu,
  NoiNhanLabel, NoiNhanItem.
- Giữ nguyên các style khác trong file gốc.
- Áp dụng cặp cỡ chữ 13 hoặc 14.
- Heading 1 Type 1: jc=center. Type 2: jc=both.
"""

from xml.etree import ElementTree as ET
from .xml_utils import parse_xml, write_xml_preserve_root_attrs, get_original_xml
from pathlib import Path
from typing import Dict


NS_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = f"{{{NS_W}}}"


def _sz_for_pair(font_pair: int, kind: str) -> int:
    """sz half-points cho cặp cỡ chữ."""
    if font_pair == 14:
        return {
            'body': 28, 'heading': 28, 'khoan': 28, 'can_cu': 28,
            'noi_nhan_label': 24, 'noi_nhan_item': 22,
        }.get(kind, 28)
    else:
        return {
            'body': 26, 'heading': 26, 'khoan': 26, 'can_cu': 26,
            'noi_nhan_label': 24, 'noi_nhan_item': 22,
        }.get(kind, 26)


# Trả về XML string cho từng style. Dùng string vì dễ debug và format đẹp.

def _normal_xml(font_pair: int) -> str:
    sz = _sz_for_pair(font_pair, 'body')
    return f'''<w:style xmlns:w="{NS_W}" w:type="paragraph" w:default="1" w:styleId="Normal">
  <w:name w:val="Normal"/>
  <w:qFormat/>
  <w:pPr>
    <w:spacing w:before="120" w:after="0" w:line="240" w:lineRule="auto"/>
    <w:ind w:firstLine="567"/>
    <w:jc w:val="both"/>
  </w:pPr>
  <w:rPr>
    <w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>
    <w:sz w:val="{sz}"/>
    <w:szCs w:val="{sz}"/>
    <w:lang w:val="vi-VN"/>
  </w:rPr>
</w:style>'''


def _heading_xml(level: int, font_pair: int, heading_type: str) -> str:
    """Build Heading1..Heading5 XML."""
    sz = _sz_for_pair(font_pair, 'heading')

    if level == 1:
        jc = 'center' if heading_type == 'type1' else 'both'
        first_line = 0 if heading_type == 'type1' else 567
        return f'''<w:style xmlns:w="{NS_W}" w:type="paragraph" w:styleId="Heading1">
  <w:name w:val="heading 1"/>
  <w:basedOn w:val="Normal"/>
  <w:next w:val="Normal"/>
  <w:qFormat/>
  <w:pPr>
    <w:keepNext/>
    <w:spacing w:before="240" w:after="120" w:line="240" w:lineRule="auto"/>
    <w:ind w:firstLine="{first_line}"/>
    <w:jc w:val="{jc}"/>
    <w:outlineLvl w:val="0"/>
  </w:pPr>
  <w:rPr>
    <w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>
    <w:b/>
    <w:bCs/>
    <w:sz w:val="{sz}"/>
    <w:szCs w:val="{sz}"/>
  </w:rPr>
</w:style>'''

    if level in (2, 3, 4):
        return f'''<w:style xmlns:w="{NS_W}" w:type="paragraph" w:styleId="Heading{level}">
  <w:name w:val="heading {level}"/>
  <w:basedOn w:val="Normal"/>
  <w:next w:val="Normal"/>
  <w:qFormat/>
  <w:pPr>
    <w:keepNext/>
    <w:spacing w:before="240" w:after="120" w:line="240" w:lineRule="auto"/>
    <w:ind w:firstLine="0"/>
    <w:jc w:val="center"/>
    <w:outlineLvl w:val="{level - 1}"/>
  </w:pPr>
  <w:rPr>
    <w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>
    <w:b/>
    <w:bCs/>
    <w:sz w:val="{sz}"/>
    <w:szCs w:val="{sz}"/>
  </w:rPr>
</w:style>'''

    if level == 5:
        # Heading5 = Điều, jc=both, firstLine=567
        return f'''<w:style xmlns:w="{NS_W}" w:type="paragraph" w:styleId="Heading5">
  <w:name w:val="heading 5"/>
  <w:basedOn w:val="Normal"/>
  <w:next w:val="Normal"/>
  <w:qFormat/>
  <w:pPr>
    <w:keepNext/>
    <w:spacing w:before="120" w:after="0" w:line="240" w:lineRule="auto"/>
    <w:ind w:firstLine="567"/>
    <w:jc w:val="both"/>
    <w:outlineLvl w:val="4"/>
  </w:pPr>
  <w:rPr>
    <w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>
    <w:b/>
    <w:bCs/>
    <w:sz w:val="{sz}"/>
    <w:szCs w:val="{sz}"/>
  </w:rPr>
</w:style>'''
    return ''


def _khoan_co_tieu_de_xml(font_pair: int) -> str:
    sz = _sz_for_pair(font_pair, 'khoan')
    return f'''<w:style xmlns:w="{NS_W}" w:type="paragraph" w:styleId="KhoanCoTieuDe">
  <w:name w:val="Khoan Co Tieu De"/>
  <w:basedOn w:val="Normal"/>
  <w:next w:val="Normal"/>
  <w:qFormat/>
  <w:pPr>
    <w:keepNext/>
    <w:spacing w:before="120" w:after="0" w:line="240" w:lineRule="auto"/>
    <w:ind w:firstLine="567"/>
    <w:jc w:val="both"/>
  </w:pPr>
  <w:rPr>
    <w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>
    <w:b/>
    <w:bCs/>
    <w:sz w:val="{sz}"/>
    <w:szCs w:val="{sz}"/>
  </w:rPr>
</w:style>'''


def _can_cu_xml(font_pair: int) -> str:
    sz = _sz_for_pair(font_pair, 'can_cu')
    return f'''<w:style xmlns:w="{NS_W}" w:type="paragraph" w:styleId="CanCu">
  <w:name w:val="Can Cu"/>
  <w:basedOn w:val="Normal"/>
  <w:next w:val="Normal"/>
  <w:qFormat/>
  <w:pPr>
    <w:spacing w:before="120" w:after="0" w:line="240" w:lineRule="auto"/>
    <w:ind w:firstLine="567"/>
    <w:jc w:val="both"/>
  </w:pPr>
  <w:rPr>
    <w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>
    <w:i/>
    <w:iCs/>
    <w:sz w:val="{sz}"/>
    <w:szCs w:val="{sz}"/>
  </w:rPr>
</w:style>'''


def _noi_nhan_label_xml() -> str:
    return f'''<w:style xmlns:w="{NS_W}" w:type="paragraph" w:styleId="NoiNhanLabel">
  <w:name w:val="Noi Nhan Label"/>
  <w:basedOn w:val="Normal"/>
  <w:qFormat/>
  <w:pPr>
    <w:spacing w:before="120" w:after="0" w:line="240" w:lineRule="auto"/>
    <w:ind w:firstLine="0"/>
    <w:jc w:val="left"/>
  </w:pPr>
  <w:rPr>
    <w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>
    <w:b/>
    <w:bCs/>
    <w:i/>
    <w:iCs/>
    <w:sz w:val="24"/>
    <w:szCs w:val="24"/>
  </w:rPr>
</w:style>'''


def _noi_nhan_item_xml() -> str:
    return f'''<w:style xmlns:w="{NS_W}" w:type="paragraph" w:styleId="NoiNhanItem">
  <w:name w:val="Noi Nhan Item"/>
  <w:basedOn w:val="Normal"/>
  <w:qFormat/>
  <w:pPr>
    <w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/>
    <w:ind w:firstLine="0"/>
    <w:jc w:val="left"/>
  </w:pPr>
  <w:rPr>
    <w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>
    <w:sz w:val="22"/>
    <w:szCs w:val="22"/>
  </w:rPr>
</w:style>'''


def _title_xml(font_pair: int) -> str:
    sz = _sz_for_pair(font_pair, 'body')
    return f'''<w:style xmlns:w="{NS_W}" w:type="paragraph" w:styleId="Title">
  <w:name w:val="Title"/>
  <w:basedOn w:val="Normal"/>
  <w:qFormat/>
  <w:pPr>
    <w:spacing w:before="240" w:after="120" w:line="240" w:lineRule="auto"/>
    <w:ind w:firstLine="0"/>
    <w:jc w:val="center"/>
  </w:pPr>
  <w:rPr>
    <w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>
    <w:b/>
    <w:bCs/>
    <w:sz w:val="{sz}"/>
    <w:szCs w:val="{sz}"/>
  </w:rPr>
</w:style>'''


def _build_all_target_styles(font_pair: int, heading_type: str) -> Dict[str, str]:
    """Build dict {styleId: xml_string} cho tất cả style cần áp."""
    styles = {}
    styles['Normal'] = _normal_xml(font_pair)
    styles['Title'] = _title_xml(font_pair)
    for lvl in range(1, 6):
        styles[f'Heading{lvl}'] = _heading_xml(lvl, font_pair, heading_type)
    styles['KhoanCoTieuDe'] = _khoan_co_tieu_de_xml(font_pair)
    styles['CanCu'] = _can_cu_xml(font_pair)
    styles['NoiNhanLabel'] = _noi_nhan_label_xml()
    styles['NoiNhanItem'] = _noi_nhan_item_xml()
    return styles


def update_styles_xml(unpacked_dir, font_pair: int, heading_type: str,
                       report: Dict) -> Dict:
    """
    Entrypoint: cập nhật styles.xml.
    Đọc styles.xml hiện có, ghi đè / thêm các style trong target list.
    """
    styles_path = Path(unpacked_dir) / 'word' / 'styles.xml'
    if not styles_path.exists():
        # File chưa có styles.xml → tạo mới từ template tối thiểu
        _create_minimal_styles_xml(styles_path)

    tree = parse_xml(styles_path)
    root = tree.getroot()

    target_styles = _build_all_target_styles(font_pair, heading_type)
    style_report = {'updated': [], 'added': []}

    # Tìm các style hiện có
    existing_styles = {}
    for style in root.findall(f'{W}style'):
        sid = style.get(f'{W}styleId')
        if sid:
            existing_styles[sid] = style

    for target_id, target_xml in target_styles.items():
        new_el = ET.fromstring(target_xml)
        if target_id in existing_styles:
            # Replace: tìm vị trí, remove cũ, insert mới
            old_el = existing_styles[target_id]
            idx = list(root).index(old_el)
            root.remove(old_el)
            root.insert(idx, new_el)
            style_report['updated'].append(target_id)
        else:
            # Append
            root.append(new_el)
            style_report['added'].append(target_id)

    write_xml_preserve_root_attrs(tree, styles_path, get_original_xml(styles_path.parent.parent, styles_path.name))

    report.setdefault('phase3', {})['styles'] = style_report
    return report


def _create_minimal_styles_xml(path: Path):
    """Tạo styles.xml tối thiểu nếu file gốc không có."""
    content = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:docDefaults>
    <w:rPrDefault>
      <w:rPr>
        <w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>
        <w:sz w:val="28"/>
        <w:szCs w:val="28"/>
        <w:lang w:val="vi-VN"/>
      </w:rPr>
    </w:rPrDefault>
    <w:pPrDefault>
      <w:pPr>
        <w:spacing w:before="120" w:after="0" w:line="240" w:lineRule="auto"/>
      </w:pPr>
    </w:pPrDefault>
  </w:docDefaults>
</w:styles>'''
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')
