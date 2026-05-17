---
name: chuan-hoa-the-thuc
description: Chuẩn hóa thể thức và kỹ thuật trình bày văn bản hành chính Việt Nam theo Nghị định số 30/2020/NĐ-CP, đồng thời sửa lỗi gõ máy và quy tắc viết hoa. Sử dụng skill này bất cứ khi nào người dùng yêu cầu chuẩn hóa, định dạng lại, format lại, sửa thể thức, áp dụng Nghị định 30, ND30, NĐ 30/2020, hoặc đề cập đến các văn bản hành chính như công văn, quyết định, tờ trình, báo cáo, thông báo, kế hoạch, nghị quyết, chỉ thị của cơ quan nhà nước Việt Nam. Cũng kích hoạt khi người dùng upload file .docx hoặc .doc và yêu cầu chuẩn hóa văn bản hành chính. Đầu ra gồm file .docx đã chuẩn hóa và báo cáo thay đổi.
---

# Chuẩn hóa văn bản hành chính theo Nghị định 30/2020/NĐ-CP

## Mục đích

Skill này nhận một file Word chứa văn bản hành chính của cơ quan nhà nước Việt Nam và trả về:

1. File `.docx` đã được chuẩn hóa thể thức, kỹ thuật trình bày theo Phụ lục I Nghị định 30/2020/NĐ-CP, sửa lỗi gõ máy, sửa quy tắc viết hoa theo Phụ lục II.
2. Báo cáo tóm tắt các thay đổi đã thực hiện, gợi ý sửa hành văn hành chính, và flag các thành phần thể thức bị thiếu.

## Khi nào dùng skill này

Dùng khi người dùng yêu cầu xử lý văn bản hành chính Việt Nam, không dùng cho:
- Hợp đồng, văn bản thương mại tư nhân.
- Sách, báo, tài liệu nghiên cứu.

## Workflow tổng

Quy trình gồm 8 giai đoạn, thực hiện tuần tự. Không bỏ giai đoạn nào, không đảo thứ tự (đặc biệt là phase nhận diện phải trước phase áp style).

```
1. Chuẩn bị file đầu vào
2. Unpack XML
3. Nhận diện loại văn bản và cặp cỡ chữ
4. Phase 1: Sửa lỗi gõ máy + viết hoa (trên text content)
5. Phase 2: Phân loại từng paragraph (component classification)
6. Phase 3: Chuẩn hóa Styles và áp pStyle / direct formatting
7. Phase 4: Chuẩn hóa Page Setup (mọi section, kể cả landscape)
8. Phase 5: Header (số trang), Phase 6: Quét bảng cụm, Phase 7: Flag + gợi ý
9. Pack lại + sinh báo cáo + present file
```

### Giai đoạn 1: Chuẩn bị file đầu vào

```bash
# Tạo workspace
mkdir -p /home/claude/nd30_work
cd /home/claude/nd30_work

# Copy file người dùng upload (đường dẫn có thể khác)
cp /mnt/user-data/uploads/<filename> input.docx

# Nếu là .doc legacy, convert sang .docx
python /mnt/skills/public/docx/scripts/office/soffice.py \
  --headless --convert-to docx input.doc
```

### Giai đoạn 2: Unpack XML

```bash
python /mnt/skills/public/docx/scripts/office/unpack.py \
  input.docx unpacked/
```

Lưu ý: `unpack.py` đã merge các adjacent runs nên không cần merge thủ công.

### Giai đoạn 3: Nhận diện loại văn bản

Đọc text content. Tìm theo thứ tự ưu tiên giảm dần:

1. **Tên loại** (in hoa, căn giữa, ngay trước Trích yếu): khớp với danh sách 29 loại trong `references/nhan-dien-loai-van-ban.md`. Đây là tín hiệu tin cậy nhất.
2. **Ký hiệu văn bản** trong "Số: NN/XXX-..." — phần XXX là viết tắt loại (QĐ, NQ, TT, CV, ...).
3. **Nếu không có Tên loại in hoa** → có thể là Công văn (Công văn không có Tên loại, chỉ có "V/v" trước trích yếu).
4. **Không xác định được** → hỏi người dùng:

   > "Tôi không xác định được loại văn bản từ nội dung file. Bạn xác nhận giúp đây là loại văn bản nào? Một số loại phổ biến: Công văn, Tờ trình, Quyết định, Báo cáo, Thông báo, Kế hoạch, Nghị quyết, Chỉ thị."

Đọc `references/nhan-dien-loai-van-ban.md` để có toàn bộ heuristics + danh sách loại.

### Giai đoạn 3b: Xác định cặp cỡ chữ

Đọc `references/chuan-ky-thuat.md` mục "Cặp cỡ chữ" để biết quy tắc 13 hoặc 14.

Heuristic:
- Quét tất cả paragraph có ≥ 200 ký tự (đảm bảo là body, không phải tiêu đề).
- Lấy cỡ chữ áp đảo (mode).
- Nếu mode = 26 (half-points, tức 13pt) → cặp 13.
- Nếu mode = 28 (14pt) → cặp 14.
- Khác → fallback cặp 14.

Ghi nhớ cặp này (gọi là `font_pair`), dùng xuyên suốt các phase sau. Mọi đoạn cỡ ≠ cặp này sẽ tự động được sửa, không hỏi, không flag.

### Giai đoạn 4: Phase 1 — Sửa lỗi gõ máy và viết hoa

```bash
python scripts/normalize.py phase1 \
  --unpacked unpacked/ \
  --report report.json
```

Phase 1 thao tác trên text content (`<w:t>...</w:t>`), không động đến formatting.

Thực hiện theo thứ tự (chi tiết trong `references/loi-go-may.md`):

1. Chuẩn hóa Unicode (NFC).
2. Chuẩn hóa khoảng trắng: ` +` → ` `, ` \n` → `\n`, tab thừa.
3. Xóa khoảng trắng trước dấu câu `,;:.!?)]}`.
4. Đảm bảo có 1 space sau dấu câu (trừ kết thúc đoạn).
5. Sửa dấu thanh sai vị trí: "hòa" → "hoà" (kiểu cũ) **hoặc** "hoà" → "hòa" (kiểu mới). Skill mặc định dùng kiểu mới (Unicode TCVN 6909), tức "hoà"/"thuý"/"oà" → "hòa"/"thúy"/"òa".
6. Sửa lỗi telex còn sót: "oo" giữa từ → "ô"/"oo" theo từ điển, tương tự "aa", "ee", "dd".
7. Áp từ điển lỗi chính tả phổ biến (`scripts/data/typo_dict.json`).
8. Áp quy tắc viết hoa theo Phụ lục II — đọc `references/phuluc2-viet-hoa.md`.

### Giai đoạn 5: Phase 2 — Phân loại paragraph

```bash
python scripts/normalize.py phase2 \
  --unpacked unpacked/ \
  --doc-type "<loại văn bản>" \
  --font-pair <13|14> \
  --report report.json
```

Mỗi paragraph được gán một `component_type`. Phân loại dựa trên: nội dung (regex), ngữ cảnh, formatting hiện tại.

**Bước tiên quyết: xác định cấu trúc nội dung (6a hay 6b) TRƯỚC khi phân loại.**

- **Trường hợp 6a**: văn bản có "Dieu" — cấu trúc Phan/Chuong/Muc/Tieu-muc/Dieu/Khoan/Diem.
- **Trường hợp 6b**: không có "Dieu" — cấu trúc Phan/Muc/Khoan-co-tieu-de/Diem.

**Quy tắc đẩy heading lên**: Đọc `references/chuan-ky-thuat.md` mục "Quy tắc đẩy heading". Xác định heading level thực tế dựa vào cấp cao nhất hiện diện, không phải vị trí cố định.

**Cấu trúc 1.1, 1.1.1**: flag trong báo cáo là không đúng chuẩn NĐ30, giữ nguyên body.

Component types chính:
- `quoc_hieu`, `tieu_ngu`
- `ten_co_quan_chu_quan`, `ten_co_quan_ban_hanh`
- `so_ky_hieu`, `dia_danh_ngay_thang`
- `ten_loai_van_ban`, `trich_yeu`, `trich_yeu_cong_van`
- `can_cu`
- `heading_phan`, `heading_chuong`, `heading_muc`, `heading_tieu_muc`, `heading_dieu`
- `khoan_co_tieu_de`
- `body` (khoản không tiêu đề, điểm, đoạn thường)
- `noi_nhan_label`, `noi_nhan_item`, `kinh_gui`
- `chan_ky_quyen_han`, `chan_ky_chuc_vu`, `chan_ky_ho_ten`
- `phu_luc_label`, `phu_luc_tieu_de`, `unknown`

### Giai đoạn 6: Phase 3 — Chuẩn hóa Styles + áp format

```bash
python scripts/normalize.py phase3 \
  --unpacked unpacked/ \
  --font-pair <13|14> \
  --heading-style <type1|type2> \
  --report report.json
```

Quy tắc kép — đọc kỹ:

**Áp pStyle (style-based)** cho các component lặp lại:
- `body` → `Normal`
- `heading_phan` → `Heading{N}` (N = level thực sau khi đẩy, xem `chuan-ky-thuat.md`)
- `heading_chuong` → `Heading{N}`
- `heading_muc` → `Heading{N}`
- `heading_tieu_muc` → `Heading{N}`
- `heading_dieu` → `Heading{N}`
- `khoan_co_tieu_de` → `Heading{N}` (6b) hoặc `KhoanCoTieuDe` (6a)
- `can_cu` → `CanCu`
- `noi_nhan_label` → `NoiNhanLabel`
- `noi_nhan_item` → `NoiNhanItem`
- `ten_loai_van_ban` → `Title` (ghi đè style Title)
- `trich_yeu` → `Title`
- `trich_yeu_cong_van` → `Title`

**Áp direct formatting** cho các component xuất hiện 1 lần:
- `quoc_hieu`, `tieu_ngu`
- `ten_co_quan_chu_quan`, `ten_co_quan_ban_hanh`
- `so_ky_hieu`, `dia_danh_ngay_thang`
- `chan_ky_quyen_han`, `chan_ky_chuc_vu`, `chan_ky_ho_ten`
- `kinh_gui`

Đọc `references/chuan-ky-thuat.md` để có bảng đầy đủ tham số và "Quy tắc đẩy heading".

**Cách trình bày heading Phần/Chương/Mục/Tiểu mục**: dù đẩy lên Heading 1,2,3... nhưng cách trình bày vẫn gắn với tên gốc:
- Phần/Chương: "Phần I" hoặc "Chương I" (in thường) trên dòng 1 + tiêu đề IN HOA trên dòng 2 trong cùng paragraph, phân cách bằng `<w:br/>` (Shift+Enter). Căn giữa.
- Mục/Tiểu mục: tương tự nhưng số Ả rập.
- Điều: một dòng, căn đều.

**Cập nhật styles.xml**: ghi đè Normal, Heading1-Heading5, Title; thêm CanCu, NoiNhanLabel, NoiNhanItem, KhoanCoTieuDe.

### Giai đoạn 7: Phase 4 — Chuẩn hóa Page Setup

```bash
python scripts/normalize.py phase4 \
  --unpacked unpacked/ \
  --report report.json
```

Quét tất cả `<w:sectPr>` (mỗi section có thể có orientation khác nhau).

Với mỗi section:
1. Đặt `<w:pgSz w:w="11906" w:h="16838"/>` cho portrait, `<w:pgSz w:orient="landscape" w:w="16838" w:h="11906"/>` cho landscape.
2. Áp `<w:pgMar>` theo nguyên tắc clamp về biên gần nhất (xem `references/chuan-ky-thuat.md` mục "Page setup linh hoạt").

**Quan trọng — Landscape margin**:
- Quy định gắn với **cạnh vật lý của tờ giấy**, không gắn với hướng.
- Trong XML của Word, `w:top` của section landscape vẫn là "cạnh trên" của trang theo hướng đọc, tức là cạnh dài 29.7cm trở thành cạnh "ngang" hiển thị.
- Phải xác minh: trong landscape, `w:left` luôn là cạnh ngắn 21cm (gáy trái khi đọc), `w:top` luôn là cạnh dài 29.7cm.
- Áp dụng: portrait và landscape đều có `top` 20-25mm, `bottom` 20-25mm, `left` 30-35mm, `right` 15-20mm.

[Suy luận] Lưu ý XML semantics: với section landscape, OOXML giữ nguyên ý nghĩa `w:top`/`w:left` theo hướng đọc của trang đã xoay. Tức là cùng giá trị `<w:pgMar w:top="1418" w:left="1985" ...>` áp cho cả portrait và landscape là đúng quy định.

### Giai đoạn 8: Phase 5 — Header (số trang)

```bash
python scripts/normalize.py phase5 \
  --unpacked unpacked/ \
  --font-pair <13|14> \
  --report report.json
```

Quy tắc:
- Đánh số trang từ 1 ngay trang đầu tiên.
- `<w:titlePg/>` trong section đầu tiên để ẩn số trang đầu (nhưng trang thứ 2 hiển thị số 2).
- Header chứa duy nhất một paragraph: căn giữa, font Times New Roman, cỡ chữ = cặp cỡ chữ body (13 hoặc 14), kiểu đứng, không đậm.
- Nội dung: `<w:fldSimple w:instr="PAGE">` để Word tự đánh.
- Áp dụng cho mọi section (portrait + landscape).

Chi tiết XML trong `references/chuan-ky-thuat.md` mục "Header XML".

### Giai đoạn 9: Phase 6 — Quét bảng cụm

```bash
python scripts/normalize.py phase6 \
  --unpacked unpacked/ \
  --report report.json
```

Xác định 2 bảng đặc trưng:
- **Bảng cụm Quốc hiệu + Tên cơ quan** (đầu văn bản, 2 cột): cột trái chứa Tên cơ quan, cột phải chứa Quốc hiệu+Tiêu ngữ.
- **Bảng cụm Nơi nhận + Chân ký** (cuối văn bản, 2 cột): cột trái chứa Nơi nhận, cột phải chứa Chức vụ+Họ tên.

Với mỗi bảng:
1. Đảm bảo `<w:tblBorders>` đều `<w:nil/>` (trong suốt) — giữ trạng thái này nếu đã có, không thay đổi nếu bảng cố ý có viền (flag thay vào báo cáo).
2. Tính tổng width = `<w:tblW>` + `<w:tblInd>`. So sánh với `content_width = page_width - left_margin - right_margin`.
3. Nếu tổng > content_width → thu nhỏ proportional về vừa content_width. Báo cáo.
4. **Không** can thiệp vào `<w:spacing w:val>` character spacing condensed trong các run — tôn trọng bản gốc.

### Giai đoạn 10: Phase 7 — Flag và gợi ý hành văn

```bash
python scripts/normalize.py phase7 \
  --unpacked unpacked/ \
  --report report.json
```

Flag (thành phần thiếu hoặc sai vị trí):
- Quốc hiệu, Tiêu ngữ, Tên cơ quan, Số ký hiệu, Địa danh, Trích yếu, Nội dung, Chân ký, Nơi nhận.
- Với văn bản không phải Công văn: thiếu Tên loại.
- Bảng cụm bị tắt viền nhưng vượt content margin.
- Thứ tự thành phần sai (vd: Quốc hiệu đặt sau Số ký hiệu).

Gợi ý hành văn (Claude tự sinh, không hardcode): Sau khi script phase7 kết thúc, đọc lại text content của file và:
- Tìm các câu rườm rà (>= 40 từ, hoặc lặp cấu trúc động từ).
- Tìm các từ chưa chuẩn mực hành chính.
- Tìm các đoạn có thể gây hiểu nhầm pháp lý (mệnh đề điều kiện không rõ chủ thể, đại từ không rõ tham chiếu).
- Trả về dưới dạng danh sách trong báo cáo, format: `Đoạn X | Trích đoạn | Nhận xét | Gợi ý sửa`.

Lưu ý: phần này dùng phán đoán ngôn ngữ của Claude — không sửa tự động, chỉ gợi ý để người dùng đọc lại.

### Giai đoạn 11: Pack + sinh báo cáo + present

```bash
# Pack lại
python /mnt/skills/public/docx/scripts/office/pack.py \
  unpacked/ output.docx --original input.docx

# Validate
python /mnt/skills/public/docx/scripts/office/validate.py output.docx

# Copy sang outputs
mkdir -p /mnt/user-data/outputs
cp output.docx /mnt/user-data/outputs/<tên gốc>_chuanhoa.docx

# Sinh báo cáo
python scripts/normalize.py report \
  --report report.json \
  --output /mnt/user-data/outputs/<tên gốc>_baocao.md
```

Cuối cùng:
```bash
# present cho người dùng
present_files(["<tên gốc>_chuanhoa.docx", "<tên gốc>_baocao.md"])
```

## Cấu trúc báo cáo đầu ra

Báo cáo theo template cố định trong `references/template-bao-cao.md`. Tóm tắt cấu trúc:

```markdown
# Báo cáo chuẩn hóa văn bản
**File gốc:** <tên>
**File chuẩn hóa:** <tên>_chuanhoa.docx
**Loại văn bản nhận diện:** ...
**Cặp cỡ chữ áp dụng:** 13 hoặc 14

## 1. Lỗi đã sửa tự động
### 1.1. Lỗi gõ máy (Phase 1)
| Loại lỗi | Số chỗ | Ví dụ |

### 1.2. Quy tắc viết hoa (Phase 1)
| Vị trí | Trước | Sau |

### 1.3. Chuẩn hóa thể thức (Phase 2-5)
- Page setup: ...
- Styles cập nhật: ...
- Components đã phân loại: ... 

## 2. Cảnh báo: Thành phần thiếu hoặc sai (Phase 6-7)
- [Thiếu] ...
- [Sai vị trí] ...
- [Bảng cụm vượt margin] ...

## 3. Gợi ý sửa hành văn (Claude phân tích)
| Đoạn | Trích | Nhận xét | Gợi ý |
```

## Reference files

Đọc các file dưới đây khi cần chi tiết:

| File | Khi nào đọc |
|---|---|
| `references/phuluc1-the-thuc.md` | Cần tra nguyên văn quy định thể thức của một thành phần cụ thể |
| `references/phuluc2-viet-hoa.md` | Phase 1 — áp quy tắc viết hoa |
| `references/chuan-ky-thuat.md` | Phase 3-5 — bảng tham số kỹ thuật, styles XML template, header XML |
| `references/nhan-dien-loai-van-ban.md` | Phase 3 — heuristics và danh sách 29 loại văn bản |
| `references/loi-go-may.md` | Phase 1 — danh sách lỗi gõ máy + regex |
| `references/template-bao-cao.md` | Phase cuối — format báo cáo |

## Nguyên tắc xử lý lỗi

- Nếu file đầu vào không phải `.docx` hoặc `.doc` → thông báo định dạng không hỗ trợ.
- Nếu file đầu vào bị mã hóa hoặc hỏng → thông báo lỗi cụ thể, không cố sửa.
- Nếu giai đoạn 3 (nhận diện) không xác định được → hỏi người dùng, không đoán.
- Nếu Phase nào ném exception → ghi vào báo cáo, tiếp tục các Phase sau (graceful degradation), miễn là output cuối cùng vẫn validate được.
- Validate sau pack: nếu fail, unpack + fix + repack tối đa 2 lần. Vẫn fail → trả lỗi cho người dùng.

## Lưu ý vận hành quan trọng

1. **Không tự thêm thành phần thiếu**. Chỉ flag.
2. **Không sửa hành văn**. Chỉ gợi ý.
3. **Không can thiệp** character spacing condensed của các run nếu bản gốc đã set.
4. **Tôn trọng cấu trúc bảng cụm**: chỉ thu hẹp width nếu vượt margin, không tách bảng thành paragraph thường.
5. **Mỗi section riêng**: page setup phải áp cho từng section, không chỉ section đầu.
6. **Trộn cặp cỡ chữ**: tự sửa, không hỏi, không flag (theo yêu cầu người dùng).
7. **Header**: áp cho mọi section, mọi orientation.
