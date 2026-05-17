# Tham số kỹ thuật chuẩn hóa văn bản hành chính

Đây là tài liệu tham chiếu cốt lõi cho Phase 3-5. Mọi tham số áp vào file đều phải đọc từ đây, không hardcode trong script trừ khi tham chiếu rõ.

## Đơn vị đo

- **Twips** (Twentieths of a Point): đơn vị OOXML chuẩn. `1 inch = 1440 twips`, `1 mm ≈ 56.7 twips`, `1 cm ≈ 567 twips`, `1 pt = 20 twips`.
- **Half-points** (`<w:sz w:val="...">`): đơn vị cỡ chữ. `cỡ chữ pt = half-point / 2`. Cỡ 13pt = 26, cỡ 14pt = 28.
- **Spacing line** (`<w:spacing w:line="..." w:lineRule="auto">`): với `lineRule="auto"`, đơn vị là 1/240 line. `line=240` = single, `line=360` = 1.5, `line=276` = 1.15.

## Cặp cỡ chữ

Theo footnote Phụ lục I Nghị định 30/2020/NĐ-CP: "Cỡ chữ trong cùng một văn bản tăng, giảm phải thống nhất."

| Component | Cặp 14 (mặc định) | Cặp 13 |
|---|---|---|
| Quốc hiệu | 13 (sz=26) | 12 (sz=24) |
| Tiêu ngữ | 14 (sz=28) | 13 (sz=26) |
| Tên cơ quan chủ quản | 13 (sz=26) | 12 (sz=24) |
| Tên cơ quan ban hành | 13 (sz=26) | 12 (sz=24) |
| Số, ký hiệu | 13 (sz=26) | 13 (sz=26) — quy định cứng 13 |
| Địa danh, ngày tháng | 14 (sz=28) | 13 (sz=26) |
| Tên loại văn bản | 14 (sz=28) | 13 (sz=26) |
| Trích yếu (văn bản có tên loại) | 14 (sz=28) | 13 (sz=26) |
| Trích yếu Công văn (V/v) | 13 (sz=26) | 12 (sz=24) |
| Body / Khoản / Điểm | 14 (sz=28) | 13 (sz=26) |
| Căn cứ | 14 (sz=28) | 13 (sz=26) |
| Heading Phần/Chương/Mục/Tiểu mục/Điều | 14 (sz=28) | 13 (sz=26) |
| Chân ký (quyền hạn, chức vụ, họ tên) | 14 (sz=28) | 13 (sz=26) |
| Kính gửi | 14 (sz=28) | 13 (sz=26) |
| Nơi nhận — nhãn "Nơi nhận:" | 12 (sz=24) | 12 (sz=24) — quy định cứng 12 |
| Nơi nhận — item | 11 (sz=22) | 11 (sz=22) — quy định cứng 11 |
| Ký hiệu người soạn thảo | 11 (sz=22) | 11 (sz=22) — quy định cứng 11 |
| Địa chỉ cơ quan/email/website | 11-12 (sz=22-24) | 11-12 (sz=22-24) |
| Số trang (header) | 14 (sz=28) | 13 (sz=26) |

## Page setup linh hoạt

Áp nguyên tắc clamp về biên gần nhất. Áp đồng nhất cho mọi section, mọi orientation.

| Tham số | Khoảng cho phép | < min → đặt = | > max → đặt = | Trong khoảng → |
|---|---|---|---|---|
| `w:top` (lề trên) | 20-25 mm | 1134 (20mm) | 1418 (25mm) | giữ |
| `w:bottom` (lề dưới) | 20-25 mm | 1134 | 1418 | giữ |
| `w:left` (lề trái) | 30-35 mm | 1701 (30mm) | 1985 (35mm) | giữ |
| `w:right` (lề phải) | 15-20 mm | 851 (15mm) | 1134 (20mm) | giữ |

Page size:
- Portrait: `<w:pgSz w:w="11906" w:h="16838"/>`
- Landscape: `<w:pgSz w:orient="landscape" w:w="16838" w:h="11906"/>`

**Lưu ý semantics OOXML cho landscape**: Với section landscape, `w:left`/`w:top` vẫn diễn giải theo hướng đọc hiển thị của trang. Tức `w:top` = cạnh trên khi nhìn vào trang đã xoay ngang (cạnh dài 29.7cm) — nhưng quy định Nghị định 30 vẫn ép `w:top` vào khoảng 20-25mm. **Không** swap giá trị giữa portrait/landscape. Cùng dải clamp.

## Spacing chung

- Line spacing body: `<w:spacing w:line="240" w:lineRule="auto"/>` (single) — đây là tối thiểu. Cho phép đến 1.5 lines (`line="360"`).
- Spacing before paragraph (body): tối thiểu 6pt = 120 twips. Áp `w:before="120"` nếu < 120, giữ nếu ≥.
- Spacing after paragraph (body): mặc định 0, hoặc theo template Doc1.docx là 60. Áp `w:after="0"`.

## Quy tắc đẩy heading

### Xác định cấu trúc (6a hay 6b)

- **6a**: văn bản có ít nhất 1 paragraph khớp `^\s*Điều\s+\d+\b`.
- **6b**: không có.

### Quy tắc đẩy heading (6a)

Thứ tự cấu trúc đầy đủ (6a): Phần → Chương → Mục → Tiểu mục → Điều.

Lập bảng `heading_present`: xét lần lượt xem văn bản có cấp nào không.

| Cấp cao nhất hiện diện | Phần | Chương | Mục | Tiểu mục | Điều |
|---|---|---|---|---|---|
| Phần | H1 | H2 | H3 | H4 | H5 |
| Chương (không có Phần) | — | H1 | H2 | H3 | H4 |
| Mục (không có Phần, Chương) | — | — | H1 | H2 | H3 |
| Tiểu mục (không có Phần, Chương, Mục) | — | — | — | H1 | H2 |
| Chỉ có Điều | — | — | — | — | H1 |

### Quy tắc đẩy heading (6b)

Thứ tự cấu trúc đầy đủ (6b): Phần → Mục → Khoản có tiêu đề.

| Cấp cao nhất hiện diện | Phần | Mục (La Mã) | Khoản có tiêu đề |
|---|---|---|---|
| Phần | H1 | H2 | H3 |
| Mục (không có Phần) | — | H1 | H2 |
| Chỉ có Khoản có tiêu đề | — | — | không áp Heading |

**Khi không áp Heading cho Khoản có tiêu đề**: gán style `KhoanCoTieuDe`.

### Cách trình bày heading gắn với tên gốc (không gắn với số thứ tự Heading)

Cách trình bày luôn gắn với **tên gốc thực thể** (Phần, Chương, Mục...), bất kể nó đang là Heading mấy sau khi đẩy:

| Thực thể | Trình bày |
|---|---|
| Phần | "Phần I" (in thường) — `<w:br/>` — "TÊN PHẦN" (in hoa). Cùng paragraph. Căn giữa. |
| Chương | "Chương I" (in thường) — `<w:br/>` — "TÊN CHƯƠNG" (in hoa). Cùng paragraph. Căn giữa. |
| Mục (6a, số Ả rập) | "Mục 1" (in thường) — `<w:br/>` — "TÊN MỤC" (in hoa). Cùng paragraph. Căn giữa. |
| Tiểu mục (6a, số Ả rập) | "Tiểu mục 1" (in thường) — `<w:br/>` — "TÊN TIỂU MỤC" (in hoa). Cùng paragraph. Căn giữa. |
| Mục (6b, số La Mã) | "I. TÊN MỤC" toàn bộ in hoa. Một dòng. Căn giữa. |
| Điều (6a) | "Điều N. Tên điều" (in thường, số + chấm + space). Một dòng. Căn đều. |
| Khoản có tiêu đề (6b) | "N. Tên khoản" (in thường). Một dòng. Căn đều. |

Skill **sửa tự động** khi phát hiện:
- Phần/Chương/Mục/Tiểu mục đang gộp 2 dòng thành 1 paragraph nhưng dùng Enter thường → tách + gộp lại bằng `<w:br/>`.
- Tên heading viết thường khi phải in hoa (Phần, Chương, Mục 6a+6b) → chuyển thành in hoa trong text.
- "Điều N." thiếu dấu chấm hoặc thiếu space → thêm vào.
- "Khoản N." thiếu dấu chấm hoặc thiếu space → thêm vào.
- Viết "Phần" in hoa toàn bộ ("PHẦN I") → sửa thành "Phần I".
- Viết "Chương" in hoa ("CHƯƠNG I") → sửa thành "Chương I".

### Cấu trúc không chuẩn: flag không áp heading

Các mẫu sau **không** được áp Heading, giữ nguyên body, ghi flag vào báo cáo:
- Số thứ tự kiểu `1.1`, `1.1.1`, `1.1.2` (phân cấp bằng dấu chấm lồng nhau).
- Mục đánh số kiểu `a.`, `b.`, `c.` dùng làm heading (nhầm với điểm).

Nội dung flag: "Cấu trúc số thứ tự `1.1.x` không đúng chuẩn Nghị định 30/2020/NĐ-CP. Đề nghị rà soát và chuyển sang cấu trúc Điều/Khoản/Điểm theo quy định."

### Điểm (bảng chữ cái tiếng Việt)

Điểm là Normal. Thứ tự đánh số **bắt buộc** theo bảng chữ cái tiếng Việt, đúng thứ tự sau (23 ký tự, bỏ f, j, w, z):

`a) b) c) d) đ) e) g) h) i) k) l) m) n) o) p) q) r) s) t) u) v) x) y)`

Skill **sửa tự động** khi phát hiện:
- Dùng dấu ngoặc đơn mở ở đầu: "a) " → giữ nguyên (đây là chuẩn).
- Dùng dấu chấm sau: "a. " → sửa thành "a) ".
- Dùng dấu ngoặc đơn đóng và mở: "(a) " → sửa thành "a) ".
- Sai thứ tự: "a, b, c, e, f..." (bỏ "đ", thêm "f") → flag.
- Dùng số thay chữ cái: "1) 2) 3)" để đánh điểm → flag.

Tham chiếu: `Điều 9 Nghị định số 30/2020/NĐ-CP`.

### Tham chiếu Nghị định, Thông tư trong văn bản

Khi nhắc đến tên đầy đủ loại văn bản kèm số hiệu, bắt buộc có từ "số" giữa:
- Đúng: `Nghị định số 30/2020/NĐ-CP`, `Thông tư số 01/2023/TT-BNV`.
- Sai (thiếu "số"): `Nghị định 30/2020/NĐ-CP`, `Thông tư 01/2023/TT-BNV`.

Regex phát hiện: `(Nghị định|Thông tư|Quyết định|Thông báo|Chỉ thị|Hướng dẫn|Chương trình|Kế hoạch)\s+(?!số\s)\d+/`.

Sửa tự động: chèn "số " giữa tên loại và số hiệu.

**Ngoại lệ**: không áp khi đứng ở đầu câu như tên loại của chính văn bản (các paragraph type `ten_loai_van_ban`).

## Bảng tham số chi tiết theo Component

Mỗi cột "Định dạng" liệt kê: font / size (cặp 14) / kiểu / alignment / indent / spacing.

### Style-based (gán pStyle)

Heading level thực tế được tính theo quy tắc đẩy heading ở trên. Script sẽ tính `effective_level` tại runtime và map vào `Heading{effective_level}`.

| Component | pStyle mặc định | Trình bày |
|---|---|---|
| body | Normal | Times New Roman / 28 / đứng / justify / firstLine=567 / before=120 line=240 |
| heading_phan | Heading{N} | Center / đậm / 28 / firstLine=0 / before=240 after=120 line=240 keepNext |
| heading_chuong | Heading{N} | Center / đậm / 28 / firstLine=0 / before=240 after=120 line=240 keepNext |
| heading_muc | Heading{N} | Center / đậm / 28 / firstLine=0 / before=240 after=120 line=240 keepNext |
| heading_tieu_muc | Heading{N} | Center / đậm / 28 / firstLine=0 / before=240 after=120 line=240 keepNext |
| heading_dieu | Heading{N} | Justify / đậm / 28 / firstLine=567 / before=120 after=0 line=240 keepNext |
| khoan_co_tieu_de (6b có heading) | Heading{N} | Justify / đậm / 28 / firstLine=567 / before=120 line=240 keepNext |
| khoan_co_tieu_de (6a hoặc 6b không có heading) | KhoanCoTieuDe | Justify / đậm / 28 / firstLine=567 / before=120 line=240 keepNext |
| ten_loai_van_ban | Title | Center / đậm / caps / 28 / firstLine=0 / before=240 after=120 line=240 keepNext |
| trich_yeu | Title | Center / đậm / 28 / firstLine=0 / before=120 after=240 line=240 |
| trich_yeu_cong_van | Title | Center / 26 / firstLine=0 / before=120 after=240 line=240 |
| can_cu | CanCu | Justify / nghiêng / 28 / firstLine=567 / before=120 line=240 |
| noi_nhan_label | NoiNhanLabel | Left / nghiêng đậm / 24 / firstLine=0 / before=120 line=240 |
| noi_nhan_item | NoiNhanItem | Left / đứng / 22 / firstLine=0 / before=0 line=240 |

**Lưu ý Title**: ghi đè style Title của Word. Cả `ten_loai_van_ban` lẫn `trich_yeu` đều dùng Title, nhưng với tham số khác nhau được đặt qua direct override trên từng paragraph sau khi gán pStyle.

### Direct formatting (áp trực tiếp lên `<w:rPr>` và `<w:pPr>` của paragraph)

| Component | Định dạng |
|---|---|
| quoc_hieu | Times New Roman / 26 / **in hoa caps**, đứng, đậm / center / firstLine=0 / before=0 line=240 |
| tieu_ngu | Times New Roman / 28 / đứng, đậm / center / firstLine=0 / before=0 line=240 |
| ten_co_quan_chu_quan | Times New Roman / 26 / **in hoa caps**, đứng, không đậm / center / firstLine=0 / before=0 line=240 |
| ten_co_quan_ban_hanh | Times New Roman / 26 / **in hoa caps**, đứng, đậm / center / firstLine=0 / before=0 line=240 |
| so_ky_hieu | Times New Roman / 26 / đứng / center / firstLine=0 / before=0 line=240 |
| dia_danh_ngay_thang | Times New Roman / 28 / nghiêng / center / firstLine=0 / before=0 line=240 |
| kinh_gui | Times New Roman / 28 / đứng / justify / firstLine=567 / before=120 line=240 |
| chan_ky_quyen_han | Times New Roman / 28 / **in hoa caps**, đứng, đậm / center / firstLine=0 / before=0 line=240 |
| chan_ky_chuc_vu | Times New Roman / 28 / **in hoa caps**, đứng, đậm / center / firstLine=0 / before=0 line=240 |
| chan_ky_ho_ten | Times New Roman / 28 / đứng, đậm / center / firstLine=0 / before=1200 line=240 |

Lưu ý "in hoa caps": dùng `<w:caps w:val="true"/>` trong `<w:rPr>`.

**Quy ước "đậm"**: `<w:b/>` và `<w:bCs/>` đồng thời.
**Quy ước "nghiêng"**: `<w:i/>` và `<w:iCs/>` đồng thời.

**ten_loai_van_ban, trich_yeu, trich_yeu_cong_van**: gán pStyle=Title + ghi đè pPr/rPr trực tiếp để đảm bảo đúng tham số (vì mỗi loại có spacing khác nhau — xem bảng Style-based ở trên).

## Styles XML template

Bộ styles cần đảm bảo có trong `styles.xml` sau Phase 3. Nếu styles.xml hiện không có một style nào → thêm vào. Nếu có rồi → ghi đè định nghĩa.

### Style Normal

```xml
<w:style w:type="paragraph" w:default="1" w:styleId="Normal">
  <w:name w:val="Normal"/>
  <w:qFormat/>
  <w:pPr>
    <w:spacing w:before="120" w:after="0" w:line="240" w:lineRule="auto"/>
    <w:ind w:firstLine="567"/>
    <w:jc w:val="both"/>
  </w:pPr>
  <w:rPr>
    <w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>
    <w:sz w:val="28"/>
    <w:szCs w:val="28"/>
    <w:lang w:val="vi-VN"/>
  </w:rPr>
</w:style>
```

Thay `sz` thành 26 cho cặp 13.

### Style Title (ghi đè mặc định Word)

```xml
<w:style w:type="paragraph" w:styleId="Title">
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
    <w:sz w:val="28"/>
    <w:szCs w:val="28"/>
  </w:rPr>
</w:style>
```

Lưu ý: `ten_loai_van_ban`, `trich_yeu`, `trich_yeu_cong_van` đều gán `pStyle=Title`. Sau đó áp **direct pPr override** để điều chỉnh spacing riêng (vì Title chỉ định nghĩa 1 bộ tham số dùng chung):
- `ten_loai_van_ban`: keepNext=true, caps=true. Override spacing: before=240, after=120.
- `trich_yeu`: caps=false, not-italic. Override spacing: before=120, after=240.
- `trich_yeu_cong_van`: sz=26, caps=false, bold=false. Override spacing: before=120, after=240.

### Style Heading1-Heading5

Pattern chung, thay `<w:val>` của `pStyle`:

```xml
<w:style w:type="paragraph" w:styleId="Heading1">
  <w:name w:val="heading 1"/>
  <w:basedOn w:val="Normal"/>
  <w:next w:val="Normal"/>
  <w:qFormat/>
  <w:pPr>
    <w:keepNext/>
    <w:spacing w:before="240" w:after="120" w:line="240" w:lineRule="auto"/>
    <w:ind w:firstLine="0"/>
    <w:jc w:val="center"/>     <!-- "both" cho Type 2 -->
    <w:outlineLvl w:val="0"/>
  </w:pPr>
  <w:rPr>
    <w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>
    <w:b/>
    <w:bCs/>
    <w:sz w:val="28"/>
    <w:szCs w:val="28"/>
  </w:rPr>
</w:style>
```

Heading2 → outlineLvl=1, Heading3 → 2, Heading4 → 3, Heading5 → 4.

Heading5 (Điều): `<w:jc w:val="both"/>`, `<w:ind w:firstLine="567"/>`.

### Style tùy biến (custom)

#### KhoanCoTieuDe

```xml
<w:style w:type="paragraph" w:styleId="KhoanCoTieuDe">
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
    <w:sz w:val="28"/>
    <w:szCs w:val="28"/>
  </w:rPr>
</w:style>
```

#### CanCu

```xml
<w:style w:type="paragraph" w:styleId="CanCu">
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
    <w:sz w:val="28"/>
    <w:szCs w:val="28"/>
  </w:rPr>
</w:style>
```

#### NoiNhanLabel

```xml
<w:style w:type="paragraph" w:styleId="NoiNhanLabel">
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
</w:style>
```

#### NoiNhanItem

```xml
<w:style w:type="paragraph" w:styleId="NoiNhanItem">
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
</w:style>
```

## Header XML

File header (vd: `header1.xml`):

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:hdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:p>
    <w:pPr>
      <w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/>
      <w:ind w:firstLine="0"/>
      <w:jc w:val="center"/>
    </w:pPr>
    <w:r>
      <w:rPr>
        <w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>
        <w:sz w:val="28"/>
        <w:szCs w:val="28"/>
      </w:rPr>
      <w:fldChar w:fldCharType="begin"/>
    </w:r>
    <w:r>
      <w:rPr>
        <w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>
        <w:sz w:val="28"/>
      </w:rPr>
      <w:instrText xml:space="preserve">PAGE</w:instrText>
    </w:r>
    <w:r>
      <w:rPr>
        <w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>
        <w:sz w:val="28"/>
      </w:rPr>
      <w:fldChar w:fldCharType="end"/>
    </w:r>
  </w:p>
</w:hdr>
```

Trong `<w:sectPr>` của section đầu tiên, thêm:
```xml
<w:headerReference w:type="default" r:id="rIdHeaderDefault"/>
<w:titlePg/>
```

Trong `<w:sectPr>` của các section tiếp theo, không cần `<w:titlePg/>`.

Cần thêm relationship trong `word/_rels/document.xml.rels`:
```xml
<Relationship Id="rIdHeaderDefault"
  Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/header"
  Target="header_nd30.xml"/>
```

Và Content Type trong `[Content_Types].xml`:
```xml
<Override PartName="/word/header_nd30.xml"
  ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/>
```

## Component types — định nghĩa và heuristics

Heuristics nhận dạng paragraph (Phase 2). Áp theo thứ tự, paragraph đã được gán một type sẽ không bị gán lại.

### 1. Bảng cụm Quốc hiệu + Tên cơ quan (đầu văn bản)

Phát hiện table đầu tiên trong document có ≥ 2 cột, trong đó có cột chứa text khớp `^CỘNG\s*HO[ÀA]\s+XÃ\s+HỘI`. 
- Cột chứa Quốc hiệu → cell có paragraphs gán type `quoc_hieu` (paragraph 1), `tieu_ngu` (paragraph 2).
- Cột còn lại → cell có paragraphs gán type `ten_co_quan_chu_quan` (nếu có), `ten_co_quan_ban_hanh` (paragraph cuối cùng có chữ in hoa).

### 2. Số ký hiệu và Địa danh ngày tháng (sau bảng cụm đầu)

Sau bảng cụm, hoặc trong table 2 cột thứ 2 ở phần đầu:
- Paragraph khớp `^Số\s*:\s*\d+` → `so_ky_hieu`.
- Paragraph khớp `,\s*ngày\s+\d{1,2}\s+tháng\s+\d{1,2}\s+năm\s+\d{4}` → `dia_danh_ngay_thang`.

### 3. Tên loại + Trích yếu

Sau khối Quốc hiệu / Số ký hiệu:
- Paragraph in hoa, căn giữa, không có dấu chấm cuối, ngắn (< 50 ký tự) → ứng viên `ten_loai_van_ban`.
- Paragraph ngay sau, in thường, căn giữa, đậm → `trich_yeu`.
- Nếu paragraph khớp `^V/v\s+` → `trich_yeu_cong_van` (đặc thù Công văn).

### 4. Căn cứ

Paragraph khớp `^Căn\s+cứ\s+` và kết thúc bằng `;` → `can_cu`.

### 5. Headings (Phần/Chương/Mục/Tiểu mục/Điều)

- `^Phần\s+[IVX]+\b` (có thể có line break + tiêu đề ngay sau) → `heading_phan`.
- `^Chương\s+[IVX]+\b` → `heading_chuong`.
- `^Mục\s+\d+\b` → `heading_muc`.
- `^Tiểu\s+mục\s+\d+\b` → `heading_tieu_muc`.
- `^Điều\s+\d+\.\s` → `heading_dieu`.

Type 2 (không có "PHẦN"): nếu document không có paragraph khớp `^Phần\s+[IVX]+\b` nhưng có paragraph khớp `^[IVX]+\.\s+[A-ZÀ-Ỹ]` (mục La Mã in hoa) → các paragraph này là `heading_phan` (sẽ áp Heading1 type 2).

### 6. Khoản có tiêu đề

Paragraph khớp `^\d+\.\s+[A-ZÀ-Ỹ][^.]*$` (bắt đầu bằng số + dấu chấm + chữ in hoa, không kết thúc bằng dấu chấm câu trong cùng đoạn) → `khoan_co_tieu_de`.

### 7. Kính gửi (Công văn / Tờ trình)

Paragraph khớp `^Kính\s+gửi\s*:` → `kinh_gui`. Các dòng "- ..." ngay sau nếu là tên nhiều nơi nhận thì gộp vào cùng paragraph hoặc giữ riêng (tùy bản gốc).

### 8. Bảng cụm Nơi nhận + Chân ký (cuối văn bản)

Phát hiện table có 2 cột ở cuối document, trong đó có cell chứa text khớp `^Nơi\s+nhận\s*:`.
- Cột Nơi nhận: paragraph đầu (label) → `noi_nhan_label`; các paragraph tiếp theo bắt đầu bằng `-` → `noi_nhan_item`.
- Cột Chân ký: paragraph đầu (in hoa đậm, kiểu "TM. ...", "KT. ...", "TUQ. ...", "Q.", "TL.") → `chan_ky_quyen_han`. Paragraph tiếp (in hoa đậm) → `chan_ky_chuc_vu`. Paragraph cuối (in thường đậm) → `chan_ky_ho_ten`.
- Trường hợp không có quyền hạn (vd: thủ trưởng ký trực tiếp): chỉ có 2 paragraph chức vụ + họ tên.

### 9. Mặc định

Mọi paragraph chưa gán → `body` (áp Normal).
