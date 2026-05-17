"""
Sinh báo cáo Markdown từ report.json sau khi qua tất cả các phase.
"""

from datetime import datetime
from typing import Dict, List


COMPONENT_VN = {
    'quoc_hieu': 'Quốc hiệu',
    'tieu_ngu': 'Tiêu ngữ',
    'ten_co_quan_chu_quan': 'Tên cơ quan chủ quản',
    'ten_co_quan_ban_hanh': 'Tên cơ quan ban hành',
    'so_ky_hieu': 'Số, ký hiệu',
    'dia_danh_ngay_thang': 'Địa danh và ngày tháng',
    'ten_loai_van_ban': 'Tên loại văn bản',
    'trich_yeu': 'Trích yếu',
    'trich_yeu_cong_van': 'Trích yếu (Công văn V/v)',
    'can_cu': 'Căn cứ ban hành',
    'kinh_gui': 'Kính gửi',
    'heading_phan': 'Heading 1 (Phần / Mục La Mã)',
    'heading_chuong': 'Heading 2 (Chương)',
    'heading_muc': 'Heading 3 (Mục)',
    'heading_tieu_muc': 'Heading 4 (Tiểu mục)',
    'heading_dieu': 'Heading 5 (Điều)',
    'khoan_co_tieu_de': 'Khoản có tiêu đề',
    'noi_nhan_label': 'Nơi nhận (nhãn)',
    'noi_nhan_item': 'Nơi nhận (item)',
    'chan_ky_quyen_han': 'Quyền hạn người ký',
    'chan_ky_chuc_vu': 'Chức vụ người ký',
    'chan_ky_ho_ten': 'Họ tên người ký',
    'phu_luc_label': 'Nhãn Phụ lục',
    'phu_luc_tieu_de': 'Tiêu đề Phụ lục',
    'body': 'Body (Normal)',
    'unknown': 'Không xác định',
}


def _twips_to_mm(twips: int) -> float:
    """Convert twips to mm (1 mm ≈ 56.7 twips)."""
    return round(twips / 56.7, 1)


def _format_phase1(p1: Dict) -> str:
    """Format report Phase 1."""
    if not p1:
        return 'Không có lỗi gõ máy nào được sửa.\n'

    lines = []
    lines.append('| Loại lỗi | Số chỗ sửa | Ví dụ |')
    lines.append('|---|---|---|')

    if p1.get('whitespace_fixed'):
        lines.append(f'| Khoảng trắng (multi-space, tab, trim) | {p1["whitespace_fixed"]} | — |')
    if p1.get('punctuation_spacing_fixed'):
        lines.append(f'| Khoảng trắng quanh dấu câu | {p1["punctuation_spacing_fixed"]} | — |')
    if p1.get('zero_width_removed'):
        lines.append(f'| Ký tự ẩn (zero-width, NBSP) | {p1["zero_width_removed"]} | — |')
    if p1.get('capitalization_sentence_start'):
        lines.append(f'| Viết hoa đầu câu | {p1["capitalization_sentence_start"]} | — |')

    tone_list = p1.get('tone_normalized', [])
    if tone_list:
        from itertools import groupby
        # Aggregate
        agg = {}
        for c in tone_list:
            k = (c['before'], c['after'])
            agg[k] = agg.get(k, 0) + c.get('count', 1)
        total = sum(agg.values())
        examples = ', '.join(
            f'{k[0]}→{k[1]} ({v})' for k, v in list(agg.items())[:3]
        )
        lines.append(f'| Dấu thanh kiểu cũ → mới | {total} | {examples} |')

    typo_list = p1.get('typo_fixed', [])
    if typo_list:
        agg = {}
        for c in typo_list:
            k = (c['before'], c['after'])
            agg[k] = agg.get(k, 0) + c.get('count', 1)
        total = sum(agg.values())
        examples = ', '.join(
            f'{k[0]}→{k[1]} ({v})' for k, v in list(agg.items())[:3]
        )
        lines.append(f'| Chính tả phổ biến | {total} | {examples} |')

    cap_proper = p1.get('capitalization_proper_nouns', [])
    if cap_proper:
        agg = {}
        for c in cap_proper:
            k = (c['before'], c['after'])
            agg[k] = agg.get(k, 0) + c.get('count', 1)
        total = sum(agg.values())
        examples = ', '.join(
            f'"{k[0]}"→"{k[1]}"' for k, _ in list(agg.items())[:2]
        )
        lines.append(f'| Viết hoa danh từ riêng | {total} | {examples} |')

    if len(lines) == 2:  # chỉ có header
        return 'Không có lỗi gõ máy nào được sửa.\n'

    return '\n'.join(lines) + '\n'


def _format_phase3(p3: Dict) -> str:
    """Format report Phase 3."""
    lines = []
    by_type = p3.get('by_type', {})
    if by_type:
        lines.append('**Phân loại paragraph:**\n')
        lines.append('| Component | Số lượng | Cách áp |')
        lines.append('|---|---|---|')

        from .format_applier import DIRECT_TYPES, STYLE_MAP_BASE, TITLE_TYPES
        for comp, count in sorted(by_type.items(), key=lambda x: -x[1]):
            label = COMPONENT_VN.get(comp, comp)
            if comp in TITLE_TYPES:
                method = 'pStyle = `Title` + direct override'
            elif comp in DIRECT_TYPES:
                method = 'Direct formatting'
            elif comp in STYLE_MAP_BASE:
                method = f'pStyle = `{STYLE_MAP_BASE[comp]}`'
            else:
                method = 'Giữ nguyên'
            lines.append(f'| {label} | {count} | {method} |')

    styles_report = p3.get('styles', {})
    if styles_report:
        lines.append('\n**Styles trong `styles.xml`:**\n')
        updated = styles_report.get('updated', [])
        added = styles_report.get('added', [])
        if updated:
            lines.append(f'- Cập nhật: `{"`, `".join(updated)}`')
        if added:
            lines.append(f'- Thêm mới: `{"`, `".join(added)}`')

    return '\n'.join(lines) + '\n'


def _format_phase4(p4: Dict) -> str:
    """Format report Phase 4 (page setup)."""
    sections = p4.get('sections', [])
    if not sections:
        return 'Không có section nào được xử lý.\n'

    lines = [f'**Tổng số section:** {len(sections)}\n']
    lines.append('| # | Hướng | top (mm) | bottom (mm) | left (mm) | right (mm) | Trạng thái |')
    lines.append('|---|---|---|---|---|---|---|')

    for s in sections:
        b = s.get('margins_before', {})
        a = s.get('margins_after', {})
        changed = b != a
        status = 'Đã clamp về khoảng quy định' if changed else 'Giữ nguyên (trong khoảng)'
        lines.append(
            f'| {s["index"] + 1} | {s["orientation"]} | '
            f'{_twips_to_mm(b.get("top", 0))} → {_twips_to_mm(a.get("top", 0))} | '
            f'{_twips_to_mm(b.get("bottom", 0))} → {_twips_to_mm(a.get("bottom", 0))} | '
            f'{_twips_to_mm(b.get("left", 0))} → {_twips_to_mm(a.get("left", 0))} | '
            f'{_twips_to_mm(b.get("right", 0))} → {_twips_to_mm(a.get("right", 0))} | '
            f'{status} |'
        )

    return '\n'.join(lines) + '\n'


def _format_phase5(p5: Dict) -> str:
    """Format report Phase 5 (header)."""
    return (
        f'- Áp header cho {p5.get("sections_with_header", 0)} section.\n'
        f'- Ẩn số trang đầu (titlePg).\n'
        f'- Cỡ chữ header: {p5.get("font_pair", 14)}.\n'
        f'- Định dạng: căn giữa, Times New Roman, không đậm.\n'
    )


def _format_phase6(p6: Dict) -> str:
    """Format report Phase 6 (table check)."""
    tables = p6.get('tables_processed', [])
    if not tables:
        return 'Không phát hiện bảng cụm Quốc hiệu hoặc Nơi nhận-Chân ký.\n'

    lines = [f'**Content width của trang:** {_twips_to_mm(p6.get("content_width", 0))} mm\n']
    lines.append('| Bảng | Width trước (mm) | Width sau (mm) | Trạng thái |')
    lines.append('|---|---|---|---|')

    for t in tables:
        label = 'Cụm Quốc hiệu' if t['type'] == 'quoc_hieu_table' else 'Cụm Nơi nhận-Chân ký'
        wb = _twips_to_mm(t['width_before'])
        wa = _twips_to_mm(t['width_after'])
        status = 'Đã thu nhỏ vì vượt content width' if t['shrunk'] else 'Trong margin'
        lines.append(f'| {label} | {wb} | {wa} | {status} |')

    return '\n'.join(lines) + '\n'


def _format_phase7(p7: Dict) -> str:
    """Format report Phase 7 (missing components)."""
    missing = p7.get('missing_components', [])
    order_warnings = p7.get('order_warnings', [])
    nonstandard = p7.get('nonstandard_structure_flags', [])

    lines = []
    if not missing and not order_warnings and not nonstandard:
        return 'Không phát hiện thành phần thể thức bị thiếu hoặc sai vị trí.\n'

    if missing:
        lines.append('### Thành phần thiếu\n')
        for m in missing:
            lines.append(f'- **[Thiếu]** {m["label"]} — {m["description"]}')

    if order_warnings:
        lines.append('\n### Cảnh báo thứ tự\n')
        for w in order_warnings:
            lines.append(
                f'- **[Sai thứ tự]** {w["description"]} '
                f'(paragraph #{w["paragraph_index"] + 1})'
            )

    if nonstandard:
        lines.append('\n### Cấu trúc không đúng chuẩn NĐ30\n')
        for f_ in nonstandard:
            lines.append(
                f'- **[Cấu trúc không chuẩn]** Paragraph #{f_["paragraph_index"] + 1}: '
                f'`{f_["excerpt"]}` — {f_["message"]}'
            )

    return '\n'.join(lines) + '\n'


def generate_report(report: Dict, file_orig: str, file_out: str,
                     handvan_suggestions: List[Dict] = None) -> str:
    """Sinh báo cáo Markdown từ report dict."""
    if handvan_suggestions is None:
        handvan_suggestions = []

    now = datetime.now().isoformat(timespec='seconds')

    doc_type = report.get('doc_type', {}).get('name', 'Không xác định')
    confidence = report.get('doc_type', {}).get('confidence', 'unknown')
    font_pair = report.get('font_pair', 14)
    heading_type = report.get('heading_type', 'type1')

    out = []
    out.append('# Báo cáo chuẩn hóa văn bản hành chính\n')
    out.append(f'**File gốc:** `{file_orig}`  ')
    out.append(f'**File chuẩn hóa:** `{file_out}`  ')
    out.append(f'**Thời gian xử lý:** {now}  ')
    out.append('**Skill:** `chuan-hoa-the-thuc` v1.0\n')

    out.append('---\n')
    out.append('## I. Thông tin nhận diện\n')
    out.append(f'- **Loại văn bản:** {doc_type} (độ tin cậy: {confidence})')
    out.append(f'- **Cặp cỡ chữ áp dụng:** {font_pair}')
    out.append(f'- **Loại Heading 1:** '
               f'{"Type 1 (có Phần, căn giữa)" if heading_type == "type1" else "Type 2 (căn đều)"}')
    p4 = report.get('phase4', {})
    sections = p4.get('sections', [])
    portrait = sum(1 for s in sections if s['orientation'] == 'portrait')
    landscape = sum(1 for s in sections if s['orientation'] == 'landscape')
    out.append(f'- **Số section:** {len(sections)} ({portrait} portrait, {landscape} landscape)\n')

    out.append('---\n')
    out.append('## II. Lỗi đã sửa tự động\n')
    out.append('### II.1. Lỗi gõ máy và chính tả (Phase 1)\n')
    out.append(_format_phase1(report.get('phase1', {})))

    out.append('### II.2. Chuẩn hóa thể thức (Phase 2-5)\n')
    out.append('#### Page Setup\n')
    out.append(_format_phase4(p4))

    out.append('#### Styles và phân loại paragraph\n')
    out.append(_format_phase3(report.get('phase3', {})))

    out.append('#### Header (số trang)\n')
    out.append(_format_phase5(report.get('phase5', {})))

    out.append('#### Bảng cụm Quốc hiệu / Nơi nhận-Chân ký\n')
    out.append(_format_phase6(report.get('phase6', {})))

    out.append('---\n')
    out.append('## III. Cảnh báo: Thành phần thiếu hoặc sai vị trí\n')
    out.append(_format_phase7(report.get('phase7', {})))

    out.append('---\n')
    out.append('## IV. Gợi ý sửa hành văn (Claude phân tích)\n')
    if not handvan_suggestions:
        out.append('Hành văn ổn, không có gợi ý cụ thể.\n')
    else:
        out.append('| # | Đoạn | Trích | Nhận xét | Gợi ý |')
        out.append('|---|---|---|---|---|')
        for i, s in enumerate(handvan_suggestions, 1):
            excerpt = s.get('excerpt', '')[:120]
            out.append(f'| {i} | #{s.get("paragraph_index", "?")} | '
                       f'{excerpt} | {s.get("note", "")} | {s.get("suggestion", "")} |')
        out.append('')

    out.append('---\n')
    out.append('*Báo cáo được tạo tự động bởi skill `chuan-hoa-the-thuc`. '
               'Vui lòng đối chiếu với file .docx đã chuẩn hóa.*\n')

    return '\n'.join(out)
