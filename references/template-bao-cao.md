# Template báo cáo chuẩn hóa

Dùng cho đầu ra `<tên>_baocao.md`. Tất cả section đều bắt buộc, kể cả khi rỗng (in "Không có" thay vì bỏ section).

## Template

```markdown
# Báo cáo chuẩn hóa văn bản hành chính

**File gốc:** {tên file gốc}
**File chuẩn hóa:** {tên file đầu ra}
**Thời gian xử lý:** {ISO datetime}
**Phiên bản skill:** chuan-hoa-the-thuc v1.0

---

## I. Thông tin nhận diện

- **Loại văn bản:** {tên loại} (độ tin cậy: {cao|trung bình|thấp|do người dùng xác nhận})
- **Cặp cỡ chữ áp dụng:** {13|14}
- **Loại Heading 1:** {Type 1 - có "Phần" căn giữa | Type 2 - heading La Mã căn đều}
- **Số section trong văn bản:** {N} ({n_portrait} portrait, {n_landscape} landscape)

---

## II. Lỗi đã sửa tự động

### II.1. Lỗi gõ máy (Phase 1)

| Loại lỗi | Số chỗ sửa | Ví dụ (trước → sau) |
|---|---|---|
| Khoảng trắng thừa | {n} | {"A    B"} → {"A B"} |
| Khoảng trắng quanh dấu câu | {n} | {"hôm nay ,trời"} → {"hôm nay, trời"} |
| Dấu thanh kiểu cũ | {n} | {"hoà bình"} → {"hòa bình"} |
| Lỗi telex còn sót | {n} | {ví dụ hoặc "không có"} |
| Chính tả từ điển | {n} | {"sử lý"} → {"xử lý"} |
| Viết hoa đầu câu | {n} | {ví dụ} |
| Viết hoa danh từ riêng | {n} | {ví dụ} |
| Ký tự ẩn (zero-width) | {n} | — |

### II.2. Chuẩn hóa thể thức (Phase 2-5)

**Page Setup:**
- Section 1 (portrait): top {trước→sau} mm, bottom {trước→sau} mm, left {trước→sau} mm, right {trước→sau} mm. {Nếu không đổi: "trong khoảng quy định, giữ nguyên"}
- Section 2 (landscape): ...
- (lặp cho mọi section)

**Styles đã cập nhật trong styles.xml:**
- Normal: {có|không có} → cập nhật theo cặp {13|14}
- Heading1: {có|không có} → cập nhật ({Type 1 center|Type 2 justify})
- Heading2..5: cập nhật
- KhoanCoTieuDe: {thêm mới|cập nhật}
- CanCu: {thêm mới|cập nhật}
- NoiNhanLabel: {thêm mới|cập nhật}
- NoiNhanItem: {thêm mới|cập nhật}

**Phân loại paragraph (Phase 2):**

| Component | Số paragraph | Áp pStyle | Direct format |
|---|---|---|---|
| Body (Normal) | {n} | ✓ | — |
| Heading 1 (Phần / Mục La Mã) | {n} | ✓ | — |
| Heading 2 (Chương) | {n} | ✓ | — |
| Heading 3 (Mục) | {n} | ✓ | — |
| Heading 4 (Tiểu mục) | {n} | ✓ | — |
| Heading 5 (Điều) | {n} | ✓ | — |
| Khoản có tiêu đề | {n} | ✓ (KhoanCoTieuDe) | — |
| Căn cứ | {n} | ✓ (CanCu) | — |
| Nơi nhận - nhãn | {n} | ✓ (NoiNhanLabel) | — |
| Nơi nhận - item | {n} | ✓ (NoiNhanItem) | — |
| Quốc hiệu | {n} | — | ✓ |
| Tiêu ngữ | {n} | — | ✓ |
| Tên cơ quan chủ quản | {n} | — | ✓ |
| Tên cơ quan ban hành | {n} | — | ✓ |
| Số, ký hiệu | {n} | — | ✓ |
| Địa danh, ngày tháng | {n} | — | ✓ |
| Tên loại văn bản | {n} | — | ✓ |
| Trích yếu | {n} | — | ✓ |
| Trích yếu Công văn (V/v) | {n} | — | ✓ |
| Kính gửi | {n} | — | ✓ |
| Chân ký - quyền hạn | {n} | — | ✓ |
| Chân ký - chức vụ | {n} | — | ✓ |
| Chân ký - họ tên | {n} | — | ✓ |
| Không phân loại được | {n} | — | giữ nguyên |

**Cỡ chữ trộn cặp đã tự sửa:**
- {n} paragraph có cỡ chữ ngoài cặp {13|14} đã chuyển về cặp đúng.
- Chi tiết: {liệt kê các cỡ chữ trước đó và số lượng}.

**Header (số trang):**
- Áp dụng cho {N} section.
- Trang đầu: ẩn số (titlePg).
- Cỡ chữ header: {13|14}.

---

## III. Cảnh báo: Thành phần thiếu hoặc sai vị trí (Phase 6-7)

{Mỗi cảnh báo là một item. Nếu không có cảnh báo nào, in "Không phát hiện cảnh báo."}

### III.1. Thành phần thể thức thiếu

- [ ] **Thiếu Quốc hiệu**: không tìm thấy paragraph khớp "CỘNG HOÀ XÃ HỘI CHỦ NGHĨA VIỆT NAM".
- [ ] **Thiếu Tên cơ quan ban hành**: không phát hiện được khối tên cơ quan ở đầu văn bản.
- (lặp cho các thành phần khác)

### III.2. Thành phần sai vị trí

- [ ] **Số ký hiệu xuất hiện trước Tên cơ quan**: vị trí paragraph 2, đúng phải sau Tên cơ quan ban hành.
- (lặp)

### III.3. Bảng cụm vượt margin

- [ ] **Bảng cụm Quốc hiệu**: tổng width {N} mm vượt content width {M} mm. Đã tự thu nhỏ về {M} mm. **Đề nghị kiểm tra lại layout**.
- (lặp)

---

## IV. Gợi ý sửa hành văn (Claude phân tích)

{Phần này do Claude phân tích thủ công từ text content. Nếu không có gợi ý, in "Hành văn ổn, không có gợi ý cụ thể."}

| # | Đoạn (số thứ tự) | Trích | Nhận xét | Gợi ý |
|---|---|---|---|---|
| 1 | Đoạn 12 | "tiến hành thực hiện việc rà soát các văn bản đã được ban hành trong thời gian vừa qua..." | Câu rườm rà (3 động từ chồng chất: "tiến hành / thực hiện / rà soát"). | "rà soát các văn bản đã ban hành thời gian qua..." |
| 2 | Đoạn 18 | "việc xử lý đối với các trường hợp vi phạm cần được tiến hành một cách nghiêm túc" | Bị động + cụm "tiến hành một cách" rườm rà. | "Xử lý nghiêm các trường hợp vi phạm." |
| ... | ... | ... | ... | ... |

---

## V. Tóm tắt

- **Tổng số lỗi tự động đã sửa:** {tổng}
- **Tổng số cảnh báo cần xử lý thủ công:** {tổng}
- **Tổng số gợi ý sửa hành văn:** {tổng}
- **Trạng thái validation OOXML:** {Passed|Failed - chi tiết}

---

*Báo cáo này được tạo tự động bởi skill `chuan-hoa-the-thuc`. Vui lòng đối chiếu với file `.docx` đã chuẩn hóa để xác nhận thay đổi.*
```

## Lưu ý khi viết báo cáo

1. **Ngôn ngữ trang trọng, ngắn gọn**: theo phong cách văn bản hành chính.
2. **Trích đoạn ngắn**: cắt lấy 80-120 ký tự, có dấu `...` ở đầu/cuối nếu cắt giữa câu.
3. **Số thứ tự đoạn**: đếm từ 1, theo thứ tự xuất hiện trong document. Không tính paragraph rỗng.
4. **Không lạm dụng cảnh báo**: chỉ flag các thành phần thực sự thiếu hoặc thực sự sai. Không flag những thứ skill đã tự sửa.
5. **Gợi ý hành văn**: tối đa 15 gợi ý quan trọng nhất. Không quá tải người dùng.
