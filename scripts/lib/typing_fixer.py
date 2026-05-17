"""
Phase 1: Sửa lỗi gõ máy, dấu thanh, chính tả, viết hoa.
Thao tác trên text content (<w:t>...</w:t>), không đụng formatting.
"""

import re
import json
import unicodedata
from pathlib import Path
from typing import Dict, List, Tuple
from xml.etree import ElementTree as ET
from .xml_utils import parse_xml, write_xml_preserve_root_attrs, get_original_xml


# Namespaces OOXML
NS_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
ET.register_namespace('w', NS_W)


# --- Bảng dấu thanh kiểu cũ → kiểu mới ---
TONE_OLD_TO_NEW = {
    'oà': 'òa', 'oá': 'óa', 'oả': 'ỏa', 'oã': 'õa', 'oạ': 'ọa',
    'Oà': 'Òa', 'Oá': 'Óa', 'Oả': 'Ỏa', 'Oã': 'Õa', 'Oạ': 'Ọa',
    'oè': 'òe', 'oé': 'óe', 'oẻ': 'ỏe', 'oẽ': 'õe', 'oẹ': 'ọe',
    'Oè': 'Òe', 'Oé': 'Óe', 'Oẻ': 'Ỏe', 'Oẽ': 'Õe', 'Oẹ': 'Ọe',
    'uỳ': 'ùy', 'uý': 'úy', 'uỷ': 'ủy', 'uỹ': 'ũy', 'uỵ': 'ụy',
    'Uỳ': 'Ùy', 'Uý': 'Úy', 'Uỷ': 'Ủy', 'Uỹ': 'Ũy', 'Uỵ': 'Ụy',
}

# Phụ âm tiếng Việt (cho regex tone normalize)
CONSONANTS = 'bcdđghklmnpqrstvxBCDĐGHKLMNPQRSTVX'


def fix_unicode_nfc(text: str) -> Tuple[str, int]:
    """NFC normalization."""
    new = unicodedata.normalize('NFC', text)
    return new, (1 if new != text else 0)


def remove_zero_width(text: str) -> Tuple[str, int]:
    """Xóa zero-width chars, convert NBSP → space."""
    count = 0
    for ch in ['\u200b', '\u200c', '\u200d', '\ufeff']:
        count += text.count(ch)
        text = text.replace(ch, '')
    nbsp_count = text.count('\u00a0')
    text = text.replace('\u00a0', ' ')
    return text, count + nbsp_count


def fix_whitespace(text: str) -> Tuple[str, int]:
    """Nhiều space → 1 space; tab → space."""
    count = 0
    # Multi-space
    new = re.sub(r' {2,}', ' ', text)
    if new != text:
        count += 1
    text = new
    # Tab
    new = re.sub(r'\t+', ' ', text)
    if new != text:
        count += 1
    text = new
    # Trim leading/trailing
    new = text.strip()
    if new != text:
        count += 1
    return new, count


def fix_punctuation_spacing(text: str) -> Tuple[str, int]:
    """Khoảng trắng quanh dấu câu."""
    count = 0

    # Loại bỏ space TRƯỚC dấu câu đóng: , ; : . ! ? ) ] }
    new = re.sub(r'\s+([,;:.!?\)\]\}])', r'\1', text)
    if new != text:
        count += 1
    text = new

    # Loại bỏ space SAU dấu mở: ( [ {
    new = re.sub(r'([\(\[\{])\s+', r'\1', text)
    if new != text:
        count += 1
    text = new

    # Đảm bảo có 1 space sau , ; : ! ? (không phải dấu chấm — vì số thập phân, "1.5")
    # nhưng có dấu chấm khi sau dấu chấm là chữ cái
    new = re.sub(r'([,;:!?])(?=[^\s\d,;:!?\)\]\}])', r'\1 ', text)
    if new != text:
        count += 1
    text = new

    # Dấu chấm: thêm space sau nếu sau là chữ cái Latin/Việt
    new = re.sub(r'\.([A-ZÀ-Ỹa-zà-ỹ])', r'. \1', text)
    if new != text:
        count += 1
    text = new

    return text, count


def fix_vietnamese_tones(text: str) -> Tuple[str, List[Dict]]:
    """Chuẩn hóa dấu thanh kiểu cũ → kiểu mới (TCVN 6909:2001)."""
    changes = []
    for old, new in TONE_OLD_TO_NEW.items():
        # Áp khi tổ hợp nằm trong âm tiết có phụ âm xung quanh hoặc đầu/cuối từ
        # Pattern: (đầu từ hoặc phụ âm) + tổ hợp + (chữ cái Việt)
        pattern = rf'(\b[{CONSONANTS}h]*){re.escape(old)}(?=[a-zA-ZÀ-Ỹà-ỹ])'
        new_text, n = re.subn(pattern, rf'\1{new}', text)
        if n > 0:
            changes.append({'before': old, 'after': new, 'count': n})
            text = new_text
    return text, changes


def load_typo_dict(path: Path) -> Dict[str, str]:
    """Load từ điển lỗi chính tả."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _preserve_case(orig: str, target: str) -> str:
    """Giữ case của từ gốc khi thay thế. orig: 'Sử Lý', target: 'xử lý' → 'Xử Lý'."""
    if orig.isupper():
        return target.upper()
    if orig.islower():
        return target.lower()
    if orig[0].isupper() and orig[1:].islower():
        return target[0].upper() + target[1:].lower()
    return target


def apply_typo_dict(text: str, typo_dict: Dict[str, str]) -> Tuple[str, List[Dict]]:
    """Áp từ điển lỗi chính tả với word-boundary."""
    changes = []
    for wrong, correct in typo_dict.items():
        if wrong == correct:
            continue
        # Word-boundary case-insensitive (Vietnamese)
        pattern = re.compile(
            rf'(?<![\w]){re.escape(wrong)}(?![\w])',
            re.IGNORECASE | re.UNICODE
        )
        count = 0
        def _replace(m):
            nonlocal count
            count += 1
            return _preserve_case(m.group(0), correct)
        new_text = pattern.sub(_replace, text)
        if count > 0:
            changes.append({'before': wrong, 'after': correct, 'count': count})
            text = new_text
    return text, changes


def fix_capitalization_sentence_start(text: str) -> Tuple[str, int]:
    """Viết hoa đầu câu sau . ? ! và đầu paragraph."""
    count = 0
    # Đầu câu sau dấu chấm câu kết thúc + space
    def _upper_after_punct(m):
        nonlocal count
        count += 1
        return m.group(1) + m.group(2).upper()
    new = re.sub(r'([.!?]\s+)([a-zà-ỹ])', _upper_after_punct, text)
    text = new

    # Đầu paragraph (đầu chuỗi)
    if text and text[0].islower():
        text = text[0].upper() + text[1:]
        count += 1

    return text, count


# Capitalization cho danh từ riêng phổ biến (an toàn — list nhỏ, không hardcode tên người)
CAP_FIXED_PHRASES = [
    ('đảng cộng sản việt nam', 'Đảng Cộng sản Việt Nam'),
    ('nhà nước cộng hòa xã hội chủ nghĩa việt nam',
     'Nhà nước Cộng hòa Xã hội chủ nghĩa Việt Nam'),
    ('tết nguyên đán', 'tết Nguyên đán'),
    ('tết trung thu', 'tết Trung thu'),
    ('tết đoan ngọ', 'tết Đoan ngọ'),
    ('cách mạng tháng tám', 'Cách mạng tháng Tám'),
    ('quốc khánh', 'Quốc khánh'),
    ('chính phủ', 'Chính phủ'),
    ('quốc hội', 'Quốc hội'),
    ('thủ tướng chính phủ', 'Thủ tướng Chính phủ'),
    ('chủ tịch nước', 'Chủ tịch nước'),
    ('bộ chính trị', 'Bộ Chính trị'),
    ('ban chấp hành trung ương', 'Ban Chấp hành Trung ương'),
]


def fix_capitalization_proper_nouns(text: str) -> Tuple[str, List[Dict]]:
    """Áp danh sách danh từ riêng cần viết hoa."""
    changes = []
    for wrong, correct in CAP_FIXED_PHRASES:
        pattern = re.compile(re.escape(wrong), re.IGNORECASE)
        matches = pattern.findall(text)
        if matches:
            new_text = pattern.sub(correct, text)
            changes.append({'before': wrong, 'after': correct, 'count': len(matches)})
            text = new_text
    return text, changes


def is_protected_paragraph(p_elem: ET.Element) -> bool:
    """Paragraph có nội dung không nên sửa: trong table cụm Quốc hiệu/Tên cơ quan,
    hoặc trong dấu nháy kép (heuristic).
    Đơn giản: kiểm tra nếu paragraph nằm trong tableCell mà cell parent có chứa
    text khớp 'CỘNG HOÀ' hoặc 'CỘNG HÒA' → protected.
    Hiện tại trả về False, có thể nâng cấp sau.
    """
    return False


def process_paragraph_text(p_elem: ET.Element, typo_dict: Dict, report: Dict):
    """Áp toàn bộ Phase 1 vào text của 1 paragraph."""
    if is_protected_paragraph(p_elem):
        return

    # Gộp tất cả w:t text
    t_elems = p_elem.findall(f'.//{{{NS_W}}}t')
    if not t_elems:
        return

    # Lấy text từ mỗi w:t
    texts = [t.text or '' for t in t_elems]
    full_text = ''.join(texts)

    if not full_text.strip():
        return

    orig = full_text

    # 1. NFC
    full_text, _ = fix_unicode_nfc(full_text)

    # 2. Zero-width
    full_text, n_zw = remove_zero_width(full_text)
    report['zero_width_removed'] = report.get('zero_width_removed', 0) + n_zw

    # 3. Whitespace
    full_text, n_ws = fix_whitespace(full_text)
    report['whitespace_fixed'] = report.get('whitespace_fixed', 0) + n_ws

    # 4. Punctuation spacing
    full_text, n_punct = fix_punctuation_spacing(full_text)
    report['punctuation_spacing_fixed'] = report.get('punctuation_spacing_fixed', 0) + n_punct

    # 5. Tone normalization
    full_text, tone_changes = fix_vietnamese_tones(full_text)
    if tone_changes:
        report.setdefault('tone_normalized', []).extend(tone_changes)

    # 6. Typo dictionary
    full_text, typo_changes = apply_typo_dict(full_text, typo_dict)
    if typo_changes:
        report.setdefault('typo_fixed', []).extend(typo_changes)

    # 7. Capitalization
    full_text, n_cap = fix_capitalization_sentence_start(full_text)
    if n_cap > 0:
        report['capitalization_sentence_start'] = \
            report.get('capitalization_sentence_start', 0) + n_cap

    full_text, cap_changes = fix_capitalization_proper_nouns(full_text)
    if cap_changes:
        report.setdefault('capitalization_proper_nouns', []).extend(cap_changes)

    if full_text == orig:
        return

    # Ghi lại text vào w:t (đặt hết vào w:t đầu, xóa text các w:t còn lại)
    t_elems[0].text = full_text
    if full_text != (full_text.strip()):
        t_elems[0].set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    for t in t_elems[1:]:
        t.text = ''


def run_phase1(unpacked_dir: Path, data_dir: Path, report: Dict) -> Dict:
    """Entrypoint Phase 1."""
    typo_dict = load_typo_dict(data_dir / 'typo_dict.json')

    phase_report = {}

    doc_xml = unpacked_dir / 'word' / 'document.xml'
    tree = parse_xml(doc_xml)
    root = tree.getroot()

    for p in root.iter(f'{{{NS_W}}}p'):
        process_paragraph_text(p, typo_dict, phase_report)

    write_xml_preserve_root_attrs(tree, doc_xml, get_original_xml(doc_xml.parent.parent, doc_xml.name))

    report['phase1'] = phase_report
    return report


# Aggregate duplicate entries in tone_normalized, typo_fixed
def aggregate_changes(changes: List[Dict]) -> List[Dict]:
    agg = {}
    for c in changes:
        key = (c['before'], c['after'])
        agg[key] = agg.get(key, 0) + c.get('count', 1)
    return [{'before': k[0], 'after': k[1], 'count': v} for k, v in agg.items()]
