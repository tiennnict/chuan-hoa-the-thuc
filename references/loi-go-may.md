# Sửa lỗi gõ máy và chuẩn hóa chính tả

Áp dụng trong Phase 1. Thao tác trên text content (`<w:t>`), không động đến formatting.

## Thứ tự xử lý (quan trọng)

Thứ tự bắt buộc — đảo thứ tự có thể tạo lỗi phụ:

1. Chuẩn hóa Unicode về NFC.
2. Xử lý zero-width và ký tự ẩn.
3. Chuẩn hóa khoảng trắng.
4. Khoảng trắng quanh dấu câu.
5. Chuẩn hóa dấu thanh tiếng Việt (kiểu cũ → kiểu mới).
6. Sửa lỗi telex còn sót.
7. Áp từ điển lỗi chính tả phổ biến.
8. Áp quy tắc viết hoa (xem `phuluc2-viet-hoa.md`).

## 1. Unicode NFC

```python
import unicodedata
text = unicodedata.normalize('NFC', text)
```

Bắt buộc vì OOXML hỗ trợ cả NFC và NFD, một số font hiển thị NFD sai.

## 2. Zero-width và ký tự ẩn

Loại bỏ:
- U+200B (ZERO WIDTH SPACE)
- U+200C (ZERO WIDTH NON-JOINER)
- U+200D (ZERO WIDTH JOINER)
- U+FEFF (BOM)
- U+00A0 (NON-BREAKING SPACE) → chuyển thành space thường, **trừ khi** ở vị trí cố ý (vd: trong "Điều 1." để giữ không xuống dòng — khó phát hiện, mặc định convert hết).

Regex: `[\u200b\u200c\u200d\ufeff\u00a0]` → thay bằng `' '` cho U+00A0, `''` cho còn lại.

## 3. Khoảng trắng

| Vấn đề | Trước | Sau |
|---|---|---|
| Nhiều space liên tiếp | `"A    B"` | `"A B"` |
| Tab giữa từ | `"A\tB"` | `"A B"` |
| Trailing space | `"A "` | `"A"` |
| Leading space | `" A"` | `"A"` |
| Nhiều xuống dòng | `"\n\n\n"` | `"\n\n"` (giữ tối đa 1 dòng trắng) |

Regex:
- `r' {2,}'` → `' '`
- `r'\t+'` → `' '`
- `r' +\n'` → `'\n'`
- `r'\n +'` → `'\n'`
- `r' +$'` → `''` (từng dòng)
- `r'^ +'` → `''` (từng dòng, **trừ** dòng đầu paragraph nếu có firstLine indent — vốn không có space leading trong OOXML, nên an toàn)

Lưu ý OOXML: text trong `<w:t>` không chứa newline. Newline được biểu diễn bằng phần tử `<w:br/>`. Vì vậy regex `\n` chỉ áp dụng khi nối text từ nhiều `<w:t>` cho phân tích, không áp khi ghi lại.

## 4. Khoảng trắng quanh dấu câu

Quy tắc:
- **Không** có space **trước** các dấu: `,` `;` `:` `.` `!` `?` `)` `]` `}`.
- **Có** 1 space **sau** các dấu trên (trừ kết thúc đoạn).
- **Không** có space **sau** các dấu mở: `(` `[` `{`.
- **Có** 1 space **trước** các dấu mở (trừ đầu đoạn).

Regex cụ thể:
- `r'\s+([,;:.!?)\]}])'` → `r'\1'`
- `r'([,;:.!?])(?=[^\s])'` → `r'\1 '` — **cẩn thận**: chỉ áp khi ký tự sau là chữ/số, không phải dấu câu khác.
- `r'([(\[{])\s+'` → `r'\1'`
- `r'(?<=\S)([(\[{])'` → `r' \1'` — chỉ áp nếu trước là chữ/số.

**Trường hợp loại trừ**:
- Dấu `.` sau số: "1.", "Điều 1.", "1.1." — không thêm space nếu sau là chữ số tiếp theo của số thứ tự cùng nhóm. Khó phát hiện perfect, ưu tiên giữ regex bình thường (sẽ thêm space sau "Điều 1." là đúng), nhưng "1.1.2." có thể bị tách. Giải pháp: kiểm tra context — nếu sau dấu `.` là chữ số trong vòng 1-2 ký tự thì giữ nguyên.
- Số thập phân: "1,5 lines" → giữ nguyên, không thêm space sau `,` nếu trước và sau đều là số.
- URL, email: không can thiệp (skip nếu paragraph khớp regex URL/email).

## 5. Chuẩn hóa dấu thanh tiếng Việt

Có 2 kiểu đặt dấu thanh:
- **Kiểu cũ**: dấu đặt theo nguyên âm cố định. "hoà", "thuý", "khoẻ", "loà", "oà", "uý".
- **Kiểu mới** (TCVN 6909:2001 — kiểu Microsoft/Apple hiện đại): dấu đặt theo nguyên âm chính. "hòa", "thúy", "khỏe", "lòa", "òa", "úy".

Nghị định 30 quy định Unicode TCVN 6909:2001 → **dùng kiểu mới**.

Bảng chuyển:

| Kiểu cũ | Kiểu mới |
|---|---|
| oà | òa |
| oá | óa |
| oả | ỏa |
| oã | õa |
| oạ | ọa |
| oè | òe |
| oé | óe |
| oẻ | ỏe |
| oẽ | õe |
| oẹ | ọe |
| uỳ | ùy |
| uý | úy |
| uỷ | ủy |
| uỹ | ũy |
| uỵ | ụy |

**Phạm vi**: chỉ áp khi tổ hợp này nằm giữa từ (không phải biên từ). Vì 2 ký tự "oa", "oe", "uy" có thể nằm ở vị trí âm tiết riêng (vd: "oa oa" — tiếng khóc, "uy hiếp"). Quy tắc: chỉ chuyển khi tổ hợp nguyên âm `o`/`u` + dấu thanh + nguyên âm khác xuất hiện trong cùng âm tiết.

Heuristic đơn giản: thay thế khi tổ hợp được bao quanh bởi phụ âm hoặc biên từ + phụ âm. Regex Python (cần `re.UNICODE`):

```python
# Ví dụ cho "oà" → "òa"
re.sub(r'([bcdđghklmnpqrstvxBCDĐGHKLMNPQRSTVX])oà', r'\1òa', text)
```

Áp tất cả các cặp trong bảng trên với pattern tương tự. **Lưu ý**: kiểm tra cả phụ âm đôi ("kh", "th", "ph", "ng", "ngh", "ch", "tr", "gh", "nh", "qu"). Pattern an toàn hơn:

```python
re.sub(r'(?<=[bcdđghklmnpqrstvxBCDĐGHKLMNPQRSTVX])oà(?=[a-zA-ZÀ-Ỹ])', 'òa', text)
# hoặc dùng word boundary
re.sub(r'\b(\w*?[bcdđghklmnpqrstvx])oà(\w*)\b', r'\1òa\2', text, flags=re.IGNORECASE)
```

**Đề xuất triển khai**: dùng thư viện `vietnamese-tone-normalizer` nếu có, hoặc cài đặt regex riêng. Thư viện chuyên có độ chính xác cao hơn.

## 6. Lỗi telex còn sót

Khi gõ telex nhưng không chuyển đổi xong, các tổ hợp này còn nằm trong text:
- `aa` → `â` (khi không phải từ tiếng nước ngoài).
- `ee` → `ê`.
- `oo` → `ô`.
- `dd` → `đ`.
- `aw` → `ă`.
- `ow` → `ơ`.
- `uw` → `ư`.

**Rủi ro cao**: tiếng nước ngoài chứa các tổ hợp này hợp lệ ("Google", "Wood", "iPhone", "Bluetooth"). Tuyệt đối **không** áp regex toàn cục.

Chỉ áp khi:
- Tổ hợp nằm trong cụm có ký tự tiếng Việt khác (vd: "ddaa" → "đâ", "ddoongs" → "đông").
- Tổ hợp không thuộc danh sách tên riêng nước ngoài thông dụng.

**Đề xuất**: dùng danh sách trắng (whitelist) — chỉ sửa nếu tổ hợp khớp pattern đặc trưng telex chưa chuyển:
```
\bddaa\b → đâ
\bddoo\b → đô
\bddee\b → đê
```

Trên thực tế, lỗi này hiếm trong văn bản hành chính đã hoàn thiện. Đặt ưu tiên thấp.

## 7. Từ điển lỗi chính tả phổ biến

Lưu trong `scripts/data/typo_dict.json`. Format: `{"sai": "đúng", ...}`.

Một số entry mẫu (Phương án (b) — danh sách phổ biến, có thể mở rộng):

```json
{
  "sử lý": "xử lý",
  "sử dụng": "sử dụng",
  "trau giồi": "trau dồi",
  "chau dồi": "trau dồi",
  "trải truốt": "trải chuốt",
  "trỉ trích": "chỉ trích",
  "trỉ huy": "chỉ huy",
  "súc tích": "súc tích",
  "xuất xắc": "xuất sắc",
  "sáng lạng": "xán lạn",
  "tham quan": "tham quan",
  "thăm quan": "tham quan",
  "trí mạng": "chí mạng",
  "kiềm chế": "kiềm chế",
  "khúc triết": "khúc chiết",
  "câu truyện": "câu chuyện",
  "trân thành": "chân thành",
  "trân trọng": "trân trọng",
  "chân quý": "trân quý",
  "tựu chung": "tựu trung",
  "trìu mến": "trìu mến",
  "dao động": "dao động",
  "giao động": "dao động",
  "rông rãi": "rộng rãi",
  "sẻ chia": "sẻ chia",
  "chia sẽ": "chia sẻ",
  "san sẽ": "san sẻ",
  "đường xá": "đường sá",
  "lãng mạng": "lãng mạn",
  "tựu trường": "tựu trường",
  "khẳng khái": "khảng khái",
  "sỉ nhục": "sỉ nhục",
  "trỉa": "tỉa",
  "cọ sát": "cọ xát",
  "đảm bảo": "đảm bảo",
  "bảo đảm": "bảo đảm",
  "chia xẻ": "chia sẻ",
  "rượi": "rượu",
  "khúc khích": "khúc khích",
  "sáng kiến": "sáng kiến",
  "tuệch toạc": "tuệch toạc",
  "giả thuyết": "giả thuyết",
  "giả thiết": "giả thiết",
  "tranh chấp": "tranh chấp",
  "thừa hành": "thừa hành",
  "thừa kế": "thừa kế",
  "kế thừa": "kế thừa",
  "nhân viên": "nhân viên",
  "nhân vật": "nhân vật",
  "phong phú": "phong phú",
  "đột xuất": "đột xuất",
  "ngả nghiêng": "ngả nghiêng",
  "ngả ngớn": "ngả ngớn",
  "rẽ trái": "rẽ trái",
  "dẽ trái": "rẽ trái",
  "sẻo nhỏ": "xẻo nhỏ",
  "vô hình chung": "vô hình trung",
  "vô hình dung": "vô hình trung"
}
```

(Danh sách mẫu — script sẽ load từ JSON, dễ mở rộng).

**Quy tắc áp**:
- Khớp từ nguyên (whole word) với word boundary `\b`.
- Phân biệt hoa thường khi khớp; khi thay thế, giữ case của từ gốc:
  - "Sử lý" → "Xử lý" (hoa đầu).
  - "SỬ LÝ" → "XỬ LÝ" (toàn hoa).
  - "sử lý" → "xử lý".
- **Bỏ qua** nếu từ nằm trong:
  - Dấu nháy kép (có thể là trích dẫn nguyên văn).
  - Trong table cell có format đặc biệt (có thể là tên riêng).
  - Trong paragraph được gán type `quoc_hieu`, `tieu_ngu`, `ten_co_quan_*` (tên cố định, không sửa).

## 8. Áp quy tắc viết hoa

Đọc `phuluc2-viet-hoa.md` để có toàn bộ quy tắc. Tóm tắt các trường hợp script tự xử lý được (rule-based):

- **Đầu câu**: chữ cái đầu sau `.`, `?`, `!`, đầu paragraph → viết hoa. Regex: `([.!?]\s+)([a-zà-ỹ])` → `\1\u(\2)` (uppercase nhóm 2).
- **Sau xuống dòng**: chữ cái đầu paragraph → viết hoa (đã có trong "Đầu câu").
- **Tên các tháng âm lịch**: "tháng giêng" → "tháng Giêng", "tháng chạp" → "tháng Chạp" (chỉ khi viết bằng chữ).
- **Ngày tết**: "tết nguyên đán" → "tết Nguyên đán", "tết trung thu" → "tết Trung thu".
- **Danh từ riêng hóa**: "đảng cộng sản việt nam" → "Đảng Cộng sản Việt Nam".

Các trường hợp khác (tên người, tên cơ quan cụ thể, tên địa lý ngoại lệ) — chỉ flag và **không** sửa tự động, vì rủi ro sai cao.

## 9. Báo cáo Phase 1

Mọi thay đổi ghi vào `report.json` theo cấu trúc:

```json
{
  "phase1": {
    "unicode_nfc": 0,
    "zero_width_removed": 2,
    "whitespace_fixed": 15,
    "punctuation_spacing_fixed": 8,
    "tone_normalized": [
      {"before": "hoà bình", "after": "hòa bình", "count": 3}
    ],
    "telex_fixed": [],
    "typo_fixed": [
      {"before": "sử lý", "after": "xử lý", "count": 2}
    ],
    "capitalization_fixed": [
      {"before": "đảng cộng sản việt nam", "after": "Đảng Cộng sản Việt Nam", "location": "para 12"}
    ]
  }
}
```
