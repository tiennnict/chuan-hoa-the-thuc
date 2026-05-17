"""
Nhận diện loại văn bản hành chính từ nội dung XML.
"""

import re
import json
import unicodedata
from pathlib import Path
from typing import Dict, Optional, Tuple
from xml.etree import ElementTree as ET
from .xml_utils import parse_xml, write_xml_preserve_root_attrs, get_original_xml


NS_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _get_paragraph_text(p: ET.Element) -> str:
    """Lấy text content của paragraph."""
    texts = []
    for t in p.iter(f'{{{NS_W}}}t'):
        if t.text:
            texts.append(t.text)
    return ''.join(texts).strip()


def _get_paragraph_jc(p: ET.Element) -> str:
    """Lấy alignment của paragraph (jc)."""
    pPr = p.find(f'{{{NS_W}}}pPr')
    if pPr is None:
        return 'left'
    jc = pPr.find(f'{{{NS_W}}}jc')
    if jc is None:
        return 'left'
    return jc.get(f'{{{NS_W}}}val', 'left')


def _is_all_upper_vi(text: str) -> bool:
    """Kiểm tra text toàn chữ in hoa (Vietnamese-aware)."""
    if not text:
        return False
    # Loại bỏ space và dấu câu để so sánh
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    return all(c.isupper() for c in letters)


def _normalize_for_match(text: str) -> str:
    """Chuẩn hóa text để so sánh: bỏ dấu, lowercase, trim."""
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    return text


def load_loai_vanban(data_dir: Path) -> Dict[str, Dict]:
    """Load danh sách 29 loại văn bản."""
    with open(data_dir / 'loai_vanban.json', 'r', encoding='utf-8') as f:
        return json.load(f)


def detect_by_ten_loai(paragraphs: list, loai_dict: Dict) -> Optional[Tuple[str, str]]:
    """
    Bước 1: Nhận diện qua Tên loại văn bản (paragraph in hoa, căn giữa).
    Trả về (tên loại, độ tin cậy) hoặc None.
    """
    # Build normalized lookup
    name_lookup = {_normalize_for_match(name): name for name in loai_dict.keys()}

    for i, p in enumerate(paragraphs):
        text = _get_paragraph_text(p)
        if not text:
            continue
        if len(text) > 80 or len(text) < 3:
            continue
        if not _is_all_upper_vi(text):
            continue
        if _get_paragraph_jc(p) not in ('center',):
            continue
        # Loại bỏ ứng viên là tên cơ quan (chứa "BỘ", "UBND",...)
        text_norm = _normalize_for_match(text)
        excluded_prefixes = ['bo ', 'ubnd', 'so ', 'uy ban', 'tong cuc', 'cuc ',
                              'phong ', 'ban ', 'vien ', 'trung tam', 'cong hoa']
        if any(text_norm.startswith(p) for p in excluded_prefixes):
            continue

        # Đối sánh chính xác
        if text_norm in name_lookup:
            return (name_lookup[text_norm], 'cao')

        # Đối sánh partial (text bắt đầu bằng tên loại)
        for norm_name, real_name in name_lookup.items():
            if text_norm.startswith(norm_name + ' ') or text_norm == norm_name:
                return (real_name, 'cao')

    return None


def detect_by_ky_hieu(paragraphs: list, loai_dict: Dict) -> Optional[Tuple[str, str]]:
    """
    Bước 2: Nhận diện qua ký hiệu văn bản "Số: NN/XXX-...".
    """
    # Build abbr lookup (case-sensitive: ký hiệu thường in hoa)
    abbr_lookup = {}
    for name, info in loai_dict.items():
        if info.get('abbr'):
            abbr_lookup[info['abbr'].upper()] = name

    for p in paragraphs:
        text = _get_paragraph_text(p)
        if not text:
            continue
        # Pattern "Số: NN/ABBR-..."
        m = re.match(r'^\s*Số\s*:\s*\d+\s*/\s*([A-ZĐ]+[a-zA-Zđ]*)\s*[-/]?',
                     text, re.IGNORECASE)
        if not m:
            continue
        abbr = m.group(1).upper()
        # Trường hợp Công văn: "Số: 15/UBND-VP" → "UBND" không phải viết tắt loại
        # Heuristic: nếu abbr có trong abbr_lookup → loại tương ứng
        if abbr in abbr_lookup:
            return (abbr_lookup[abbr], 'trung bình')
        # Còn lại → có thể là Công văn (ký hiệu không phải tên loại)
        # Kiểm tra format đầy đủ "Số: NN/CQ-DV"
        m2 = re.match(r'^\s*Số\s*:\s*\d+\s*/\s*[A-ZĐ]+\s*-\s*[A-ZĐ]+',
                      text, re.IGNORECASE)
        if m2:
            return ('Công văn', 'trung bình')

    return None


def detect_by_context(paragraphs: list) -> Optional[Tuple[str, str]]:
    """
    Bước 3: Suy luận từ ngữ cảnh.
    """
    text_all = '\n'.join(_get_paragraph_text(p) for p in paragraphs[:30])
    text_norm = _normalize_for_match(text_all)

    has_vv = bool(re.search(r'\bv/v\b', text_norm))
    has_kinh_gui = 'kinh gui' in text_norm
    has_can_cu = text_norm.count('can cu ') >= 2
    has_to_trinh = 'to trinh' in text_norm
    has_bao_cao = 'bao cao' in text_norm[:200]

    if has_vv:
        return ('Công văn', 'thấp')
    if has_to_trinh and has_kinh_gui:
        return ('Tờ trình', 'thấp')
    if has_can_cu:
        return ('Quyết định', 'thấp')
    if has_bao_cao:
        return ('Báo cáo', 'thấp')

    return None


def detect_document_type(unpacked_dir: Path, data_dir: Path) -> Tuple[Optional[str], str]:
    """
    Entrypoint: nhận diện loại văn bản.
    Trả về (tên loại, độ tin cậy). Nếu không xác định: (None, 'unknown').
    """
    loai_dict = load_loai_vanban(data_dir)
    doc_xml = unpacked_dir / 'word' / 'document.xml'
    tree = parse_xml(doc_xml)
    root = tree.getroot()
    paragraphs = list(root.iter(f'{{{NS_W}}}p'))

    # Chỉ xét 50 paragraph đầu
    paragraphs_head = paragraphs[:50]

    # Bước 1: tên loại
    result = detect_by_ten_loai(paragraphs_head, loai_dict)
    if result:
        return result

    # Bước 2: ký hiệu
    result = detect_by_ky_hieu(paragraphs_head, loai_dict)
    if result:
        return result

    # Bước 3: ngữ cảnh
    result = detect_by_context(paragraphs)
    if result:
        return result

    return (None, 'unknown')


def detect_font_pair(unpacked_dir: Path) -> int:
    """
    Phát hiện cặp cỡ chữ chủ đạo: 13 hoặc 14.
    Trả về 13 hoặc 14 (số nguyên).
    """
    from collections import Counter
    doc_xml = unpacked_dir / 'word' / 'document.xml'
    tree = parse_xml(doc_xml)
    root = tree.getroot()

    # Đếm cỡ chữ trong các paragraph body (>= 200 ký tự)
    size_counter = Counter()
    for p in root.iter(f'{{{NS_W}}}p'):
        text = _get_paragraph_text(p)
        if len(text) < 200:
            continue
        for sz in p.iter(f'{{{NS_W}}}sz'):
            val = sz.get(f'{{{NS_W}}}val')
            if val:
                try:
                    size_counter[int(val)] += 1
                except ValueError:
                    pass

    if not size_counter:
        return 14  # fallback

    mode_size = size_counter.most_common(1)[0][0]
    if mode_size == 26:  # 13pt
        return 13
    if mode_size == 28:  # 14pt
        return 14
    # Khác → fallback 14
    return 14


def detect_heading_type(unpacked_dir: Path) -> str:
    """
    Phát hiện Heading 1 Type: 'type1' (có "Phần") hoặc 'type2' (chỉ có mục La Mã).
    """
    doc_xml = unpacked_dir / 'word' / 'document.xml'
    tree = parse_xml(doc_xml)
    root = tree.getroot()

    for p in root.iter(f'{{{NS_W}}}p'):
        text = _get_paragraph_text(p)
        if re.match(r'^\s*Phần\s+[IVX]+\b', text):
            return 'type1'

    return 'type2'
