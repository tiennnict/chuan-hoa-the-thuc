"""
Tiện ích XML để tránh vấn đề ElementTree làm mất namespace declaration
khi parse rồi write lại file Word XML.

Cách giải quyết:
- Đăng ký tất cả namespace OOXML phổ biến TRƯỚC khi parse.
- Sau khi write, dùng helper inject lại các xmlns: declaration bị thiếu.
"""

import re
from xml.etree import ElementTree as ET
from pathlib import Path


# Toàn bộ namespace OOXML cần đăng ký để ElementTree giữ tên prefix gốc
OOXML_NAMESPACES = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math',
    'v': 'urn:schemas-microsoft-com:vml',
    'o': 'urn:schemas-microsoft-com:office:office',
    'w10': 'urn:schemas-microsoft-com:office:word',
    'w14': 'http://schemas.microsoft.com/office/word/2010/wordml',
    'w15': 'http://schemas.microsoft.com/office/word/2012/wordml',
    'w16': 'http://schemas.microsoft.com/office/word/2018/wordml',
    'w16cex': 'http://schemas.microsoft.com/office/word/2018/wordml/cex',
    'w16cid': 'http://schemas.microsoft.com/office/word/2016/wordml/cid',
    'w16du': 'http://schemas.microsoft.com/office/word/2023/wordml/word16du',
    'w16sdtdh': 'http://schemas.microsoft.com/office/word/2020/wordml/sdtdatahash',
    'w16sdtfl': 'http://schemas.microsoft.com/office/word/2024/wordml/sdtformatlock',
    'w16se': 'http://schemas.microsoft.com/office/word/2015/wordml/symex',
    'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
    'wp14': 'http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing',
    'wpc': 'http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas',
    'wpg': 'http://schemas.microsoft.com/office/word/2010/wordprocessingGroup',
    'wpi': 'http://schemas.microsoft.com/office/word/2010/wordprocessingInk',
    'wps': 'http://schemas.microsoft.com/office/word/2010/wordprocessingShape',
    'wne': 'http://schemas.microsoft.com/office/word/2006/wordml',
    'mc': 'http://schemas.openxmlformats.org/markup-compatibility/2006',
    'cx': 'http://schemas.microsoft.com/office/drawing/2014/chartex',
    'cx1': 'http://schemas.microsoft.com/office/drawing/2015/9/8/chartex',
    'cx2': 'http://schemas.microsoft.com/office/drawing/2015/10/21/chartex',
    'cx3': 'http://schemas.microsoft.com/office/drawing/2016/5/9/chartex',
    'cx4': 'http://schemas.microsoft.com/office/drawing/2016/5/10/chartex',
    'cx5': 'http://schemas.microsoft.com/office/drawing/2016/5/11/chartex',
    'cx6': 'http://schemas.microsoft.com/office/drawing/2016/5/12/chartex',
    'cx7': 'http://schemas.microsoft.com/office/drawing/2016/5/13/chartex',
    'cx8': 'http://schemas.microsoft.com/office/drawing/2016/5/14/chartex',
    'aink': 'http://schemas.microsoft.com/office/drawing/2016/ink',
    'am3d': 'http://schemas.microsoft.com/office/drawing/2017/model3d',
    'oel': 'http://schemas.microsoft.com/office/2019/extlst',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'pic': 'http://schemas.openxmlformats.org/drawingml/2006/picture',
}


def register_namespaces():
    """Đăng ký toàn bộ namespace OOXML với ElementTree."""
    for prefix, uri in OOXML_NAMESPACES.items():
        ET.register_namespace(prefix, uri)


# Tự động đăng ký khi module được import
register_namespaces()


def parse_xml(path: Path) -> ET.ElementTree:
    """Parse file XML, đảm bảo namespace đã đăng ký."""
    register_namespaces()
    return ET.parse(str(path))


def write_xml_preserve_root_attrs(tree: ET.ElementTree, path: Path,
                                    original_path: Path = None):
    """
    Write XML, đảm bảo giữ nguyên tất cả xmlns + mc:Ignorable trên root element.

    Cách làm: đọc declaration root từ file gốc (nếu có), ghi đè dòng đầu của
    file output bằng declaration gốc.
    """
    # Ghi như bình thường trước
    tree.write(str(path), encoding='utf-8', xml_declaration=True)

    if original_path is None:
        original_path = path

    if not original_path.exists():
        return

    # Đọc opening tag từ file gốc (chứa tất cả xmlns + mc:Ignorable)
    orig_content = original_path.read_text(encoding='utf-8', errors='replace')
    # Tìm root element opening
    # Pattern: <w:document ...> hoặc <w:styles ...> hoặc <w:hdr ...>
    m = re.search(r'<(w:\w+)([^>]*?)(?:/>|>)', orig_content)
    if not m:
        return
    orig_root_name = m.group(1)
    orig_root_attrs = m.group(2)

    # Đọc lại file vừa ghi và thay opening tag
    new_content = path.read_text(encoding='utf-8')

    # Tìm root opening trong file mới
    m2 = re.search(r'<(w:\w+)([^>]*?)(?:/>|>)', new_content)
    if not m2:
        return
    new_root_name = m2.group(1)
    if new_root_name != orig_root_name:
        return  # khác root → không thay

    # Replace opening tag: giữ root name từ orig, attrs từ orig
    new_content = re.sub(
        r'<(' + re.escape(orig_root_name) + r')[^>]*?>',
        f'<{orig_root_name}{orig_root_attrs}>',
        new_content,
        count=1
    )

    path.write_text(new_content, encoding='utf-8')


def save_document_xml(unpacked_dir: Path, tree: ET.ElementTree):
    """Convenience: save document.xml giữ namespace gốc.
    Cần lưu bản gốc của document.xml trước khi sửa đổi."""
    doc_xml = Path(unpacked_dir) / 'word' / 'document.xml'
    backup = Path(unpacked_dir) / 'word' / '.document_original.xml'
    if not backup.exists():
        # Lần đầu: backup file gốc trước khi ghi đè
        # (Khi này document.xml chưa bị ghi đè - tuy nhiên với cấu trúc hiện tại
        # chúng ta đã ghi đè rồi. Cần snapshot ngay sau unpack.)
        pass
    write_xml_preserve_root_attrs(tree, doc_xml, backup if backup.exists() else None)


def snapshot_original_xmls(unpacked_dir: Path):
    """Sao lưu các file XML root quan trọng ngay sau unpack, để giữ namespace gốc."""
    import shutil
    word_dir = Path(unpacked_dir) / 'word'
    for fname in ('document.xml', 'styles.xml'):
        src = word_dir / fname
        dst = word_dir / f'.{fname}.original'
        if src.exists() and not dst.exists():
            shutil.copy2(src, dst)


def get_original_xml(unpacked_dir: Path, fname: str) -> Path:
    """Trả về đường dẫn snapshot gốc (để re-inject xmlns)."""
    return Path(unpacked_dir) / 'word' / f'.{fname}.original'


def cleanup_snapshots(unpacked_dir: Path):
    """Xóa snapshot trước khi pack."""
    word_dir = Path(unpacked_dir) / 'word'
    for p in word_dir.glob('.*.original'):
        p.unlink()
