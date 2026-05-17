#!/usr/bin/env python3
"""
Entrypoint cho skill chuan-hoa-the-thuc.

Hỗ trợ 2 chế độ:
1. Mode tổng hợp (`run`): chạy toàn bộ pipeline từ phase 1 đến phase 7.
2. Mode từng phase: cho phép Claude gọi riêng từng phase nếu cần kiểm soát chi tiết.

Usage:
    python normalize.py run --input <file.docx> --output-dir <dir>
        [--doc-type <Tên loại>] [--font-pair <13|14>]

    python normalize.py phase1 --unpacked <dir> --report <report.json>
    python normalize.py phase2 --unpacked <dir> --doc-type <Loại>
        --font-pair <13|14> --report <report.json>
    ...
"""

import argparse
import json
import sys
from pathlib import Path

# Add script dir to path for lib imports
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from lib.xml_utils import snapshot_original_xmls, cleanup_snapshots
from lib.typing_fixer import run_phase1
from lib.doc_type_detector import (
    detect_document_type, detect_font_pair, detect_heading_type
)
from lib.component_classifier import classify_all
from lib.format_applier import run_phase3
from lib.style_builder import update_styles_xml
from lib.page_setup import run_phase4, run_phase5
from lib.table_checker import run_phase6, run_phase7
from lib.report_generator import generate_report


DATA_DIR = SCRIPT_DIR / 'data'


def _load_report(path: Path) -> dict:
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def _save_report(report: dict, path: Path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)


def cmd_phase1(args):
    unpacked = Path(args.unpacked)
    report_path = Path(args.report)
    report = _load_report(report_path)
    report = run_phase1(unpacked, DATA_DIR, report)
    _save_report(report, report_path)
    print(f'[phase1] Hoàn tất. Report: {report_path}')


def cmd_detect(args):
    """Nhận diện loại văn bản, cặp cỡ chữ, heading type."""
    unpacked = Path(args.unpacked)
    report_path = Path(args.report)
    report = _load_report(report_path)

    doc_type, confidence = detect_document_type(unpacked, DATA_DIR)
    font_pair = detect_font_pair(unpacked)
    heading_type = detect_heading_type(unpacked)

    report['doc_type'] = {'name': doc_type, 'confidence': confidence}
    report['font_pair'] = font_pair
    report['heading_type'] = heading_type
    _save_report(report, report_path)

    # In ra để Claude/user đọc
    result = {
        'doc_type': doc_type,
        'confidence': confidence,
        'font_pair': font_pair,
        'heading_type': heading_type,
    }
    print(json.dumps(result, ensure_ascii=False))


def cmd_phase2(args):
    """Phase 2: phân loại paragraph."""
    unpacked = Path(args.unpacked)
    report_path = Path(args.report)
    report = _load_report(report_path)

    doc_type = args.doc_type or report.get('doc_type', {}).get('name', 'Công văn')
    heading_type = args.heading_type or report.get('heading_type', 'type1')

    result = classify_all(unpacked, doc_type, heading_type)
    classifications, level_map, structure, nonstandard_flags = result

    report['classifications'] = {str(k): v for k, v in classifications.items()}
    report['level_map'] = level_map
    report['structure'] = structure
    report['nonstandard_flags'] = nonstandard_flags
    _save_report(report, report_path)

    from collections import Counter
    summary = Counter(classifications.values())
    print(f'[phase2] Cấu trúc: {structure}. Level map: {level_map}')
    print(f'[phase2] Phân loại {len(classifications)} paragraph:')
    for k, v in summary.most_common():
        print(f'  {k}: {v}')
    if nonstandard_flags:
        print(f'[phase2] Cảnh báo: {len(nonstandard_flags)} đoạn dùng cấu trúc 1.1.x không chuẩn.')


def cmd_phase3(args):
    """Phase 3: áp định dạng + cập nhật styles."""
    unpacked = Path(args.unpacked)
    report_path = Path(args.report)
    report = _load_report(report_path)

    font_pair = args.font_pair or report.get('font_pair', 14)
    heading_type = args.heading_type or report.get('heading_type', 'type1')
    classifications_str = report.get('classifications', {})
    classifications = {int(k): v for k, v in classifications_str.items()}
    level_map = report.get('level_map', {})

    if not classifications:
        print('[phase3] LỖI: chưa có classifications từ Phase 2. '
              'Chạy `phase2` trước.', file=sys.stderr)
        sys.exit(1)

    update_styles_xml(unpacked, font_pair, heading_type, report)
    run_phase3(unpacked, classifications, font_pair, heading_type, report,
               level_map=level_map)

    _save_report(report, report_path)
    print(f'[phase3] Hoàn tất.')


def cmd_phase4(args):
    """Phase 4: page setup."""
    unpacked = Path(args.unpacked)
    report_path = Path(args.report)
    report = _load_report(report_path)
    run_phase4(unpacked, report)
    _save_report(report, report_path)
    sections = report.get('phase4', {}).get('sections', [])
    print(f'[phase4] Xử lý {len(sections)} section.')


def cmd_phase5(args):
    """Phase 5: header."""
    unpacked = Path(args.unpacked)
    report_path = Path(args.report)
    report = _load_report(report_path)
    font_pair = args.font_pair or report.get('font_pair', 14)
    run_phase5(unpacked, font_pair, report)
    _save_report(report, report_path)
    print(f'[phase5] Hoàn tất.')


def cmd_phase6(args):
    """Phase 6: kiểm tra bảng cụm."""
    unpacked = Path(args.unpacked)
    report_path = Path(args.report)
    report = _load_report(report_path)
    run_phase6(unpacked, report)
    _save_report(report, report_path)
    p6 = report.get('phase6', {})
    print(f'[phase6] Xử lý {len(p6.get("tables_processed", []))} bảng. '
          f'Thu nhỏ {len(p6.get("tables_shrunk", []))} bảng.')


def cmd_phase7(args):
    """Phase 7: flag thành phần thiếu."""
    unpacked = Path(args.unpacked)
    report_path = Path(args.report)
    report = _load_report(report_path)

    doc_type = args.doc_type or report.get('doc_type', {}).get('name', 'Công văn')
    classifications_str = report.get('classifications', {})
    classifications = {int(k): v for k, v in classifications_str.items()}

    run_phase7(unpacked, classifications, doc_type, report)
    _save_report(report, report_path)

    p7 = report.get('phase7', {})
    missing = p7.get('missing_components', [])
    if missing:
        print(f'[phase7] Phát hiện {len(missing)} thành phần thiếu:')
        for m in missing:
            print(f'  - {m["label"]}')
    else:
        print('[phase7] Đủ thành phần.')


def cmd_report(args):
    """Sinh báo cáo Markdown."""
    report_path = Path(args.report)
    out_path = Path(args.output)
    report = _load_report(report_path)

    # Đọc handvan suggestions (nếu có)
    handvan = []
    if args.handvan:
        handvan_path = Path(args.handvan)
        if handvan_path.exists():
            with open(handvan_path, 'r', encoding='utf-8') as f:
                handvan = json.load(f)

    md = generate_report(
        report,
        file_orig=args.file_orig or 'input.docx',
        file_out=args.file_out or 'output.docx',
        handvan_suggestions=handvan,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(md, encoding='utf-8')
    print(f'[report] Đã ghi {out_path}')


def cmd_run(args):
    """Chạy toàn bộ pipeline."""
    import shutil
    import subprocess

    input_path = Path(args.input).resolve()
    if not input_path.exists():
        print(f'LỖI: file {input_path} không tồn tại.', file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Tạo workspace
    work = output_dir / '_work'
    work.mkdir(exist_ok=True)

    # Copy input vào workspace
    if input_path.suffix.lower() == '.doc':
        # Convert .doc → .docx
        shutil.copy(input_path, work / 'input.doc')
        result = subprocess.run([
            'python', '/mnt/skills/public/docx/scripts/office/soffice.py',
            '--headless', '--convert-to', 'docx',
            str(work / 'input.doc')
        ], capture_output=True, text=True, cwd=work)
        if result.returncode != 0:
            print(f'LỖI convert .doc → .docx: {result.stderr}', file=sys.stderr)
            sys.exit(1)
        docx_path = work / 'input.docx'
    else:
        docx_path = work / 'input.docx'
        shutil.copy(input_path, docx_path)

    # Unpack
    unpacked = work / 'unpacked'
    result = subprocess.run([
        'python', '/mnt/skills/public/docx/scripts/office/unpack.py',
        str(docx_path), str(unpacked)
    ], capture_output=True, text=True)
    if result.returncode != 0:
        print(f'LỖI unpack: {result.stderr}', file=sys.stderr)
        sys.exit(1)

    # Snapshot original XMLs để giữ namespace declarations gốc
    snapshot_original_xmls(unpacked)

    report_path = work / 'report.json'
    report = {}
    _save_report(report, report_path)

    # === Detect ===
    print('--- Phase: Nhận diện ---')
    doc_type, confidence = detect_document_type(unpacked, DATA_DIR)
    font_pair = args.font_pair or detect_font_pair(unpacked)
    heading_type = detect_heading_type(unpacked)

    # Nếu --doc-type được pass và doc_type hiện tại là None hoặc tin cậy thấp
    if args.doc_type:
        doc_type = args.doc_type
        confidence = 'do người dùng xác nhận'
    elif doc_type is None:
        print('CẢNH BÁO: không xác định được loại văn bản. '
              'Hãy chạy lại với --doc-type "<Loại>".', file=sys.stderr)
        doc_type = 'Không xác định'
        confidence = 'unknown'

    print(f'  doc_type: {doc_type} ({confidence})')
    print(f'  font_pair: {font_pair}')
    print(f'  heading_type: {heading_type}')

    report['doc_type'] = {'name': doc_type, 'confidence': confidence}
    report['font_pair'] = font_pair
    report['heading_type'] = heading_type
    _save_report(report, report_path)

    # === Phase 1 ===
    print('--- Phase 1: Sửa lỗi gõ máy + viết hoa ---')
    run_phase1(unpacked, DATA_DIR, report)
    _save_report(report, report_path)

    # === Phase 2 ===
    print('--- Phase 2: Phân loại paragraph ---')
    classifications, level_map, structure, nonstandard_flags = \
        classify_all(unpacked, doc_type, heading_type)
    report['classifications'] = {str(k): v for k, v in classifications.items()}
    report['level_map'] = level_map
    report['structure'] = structure
    report['nonstandard_flags'] = nonstandard_flags
    _save_report(report, report_path)
    if nonstandard_flags:
        print(f'  Cảnh báo: {len(nonstandard_flags)} đoạn dùng cấu trúc 1.1.x không chuẩn.')

    # === Phase 3 ===
    print('--- Phase 3: Chuẩn hóa Styles + áp định dạng ---')
    update_styles_xml(unpacked, font_pair, heading_type, report)
    run_phase3(unpacked, classifications, font_pair, heading_type, report,
               level_map=level_map)
    _save_report(report, report_path)

    # === Phase 4 ===
    print('--- Phase 4: Page Setup ---')
    run_phase4(unpacked, report)
    _save_report(report, report_path)

    # === Phase 5 ===
    print('--- Phase 5: Header (số trang) ---')
    run_phase5(unpacked, font_pair, report)
    _save_report(report, report_path)

    # === Phase 6 ===
    print('--- Phase 6: Kiểm tra bảng cụm ---')
    run_phase6(unpacked, report)
    _save_report(report, report_path)

    # === Phase 7 ===
    print('--- Phase 7: Flag thành phần thiếu ---')
    run_phase7(unpacked, classifications, doc_type, report)
    _save_report(report, report_path)

    # === Pack ===
    print('--- Pack lại file .docx ---')
    # Xóa snapshots trước khi pack
    cleanup_snapshots(unpacked)
    out_name = input_path.stem + '_chuanhoa.docx'
    output_docx = output_dir / out_name
    result = subprocess.run([
        'python', '/mnt/skills/public/docx/scripts/office/pack.py',
        str(unpacked), str(output_docx),
        '--original', str(docx_path)
    ], capture_output=True, text=True)
    if result.returncode != 0:
        print(f'LỖI pack: {result.stderr}', file=sys.stderr)
        sys.exit(1)

    # === Report ===
    print('--- Sinh báo cáo ---')
    report_md_path = output_dir / (input_path.stem + '_baocao.md')
    md = generate_report(report,
                         file_orig=input_path.name,
                         file_out=out_name,
                         handvan_suggestions=[])  # Claude sẽ thêm sau
    report_md_path.write_text(md, encoding='utf-8')

    print(f'\nHoàn tất.')
    print(f'  File chuẩn hóa: {output_docx}')
    print(f'  Báo cáo: {report_md_path}')
    print(f'  Report JSON (chi tiết): {report_path}')


def main():
    parser = argparse.ArgumentParser(
        description='Chuẩn hóa văn bản hành chính theo Nghị định 30/2020/NĐ-CP')
    sub = parser.add_subparsers(dest='cmd', required=True)

    # run (tất cả)
    p_run = sub.add_parser('run', help='Chạy toàn bộ pipeline')
    p_run.add_argument('--input', required=True, help='File .docx hoặc .doc')
    p_run.add_argument('--output-dir', required=True, help='Thư mục đầu ra')
    p_run.add_argument('--doc-type', help='Loại văn bản (nếu skill không tự nhận được)')
    p_run.add_argument('--font-pair', type=int, choices=[13, 14],
                       help='Cặp cỡ chữ (mặc định auto-detect)')
    p_run.set_defaults(func=cmd_run)

    # phase commands
    for phase_name, func in [
        ('detect', cmd_detect),
        ('phase1', cmd_phase1),
        ('phase2', cmd_phase2),
        ('phase3', cmd_phase3),
        ('phase4', cmd_phase4),
        ('phase5', cmd_phase5),
        ('phase6', cmd_phase6),
        ('phase7', cmd_phase7),
    ]:
        p = sub.add_parser(phase_name, help=f'Chạy riêng {phase_name}')
        p.add_argument('--unpacked', required=True)
        p.add_argument('--report', required=True)
        p.add_argument('--doc-type')
        p.add_argument('--font-pair', type=int, choices=[13, 14])
        p.add_argument('--heading-type', choices=['type1', 'type2'])
        p.set_defaults(func=func)

    # report
    p_rep = sub.add_parser('report', help='Sinh báo cáo Markdown')
    p_rep.add_argument('--report', required=True)
    p_rep.add_argument('--output', required=True)
    p_rep.add_argument('--file-orig', default='input.docx')
    p_rep.add_argument('--file-out', default='output.docx')
    p_rep.add_argument('--handvan', help='Đường dẫn file JSON chứa gợi ý hành văn')
    p_rep.set_defaults(func=cmd_report)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
