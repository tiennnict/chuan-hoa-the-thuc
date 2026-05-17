# Nhận diện loại văn bản hành chính

## Danh sách 29 loại văn bản hành chính (Điều 7 Nghị định 30/2020/NĐ-CP)

| # | Tên đầy đủ | Viết tắt (ký hiệu) | Có tên loại? |
|---|---|---|---|
| 1 | Nghị quyết (cá biệt) | NQ | Có |
| 2 | Quyết định (cá biệt) | QĐ | Có |
| 3 | Chỉ thị | CT | Có |
| 4 | Quy chế | QC | Có |
| 5 | Quy định | QyĐ | Có |
| 6 | Thông cáo | TC | Có |
| 7 | Thông báo | TB | Có |
| 8 | Hướng dẫn | HD | Có |
| 9 | Chương trình | CTr | Có |
| 10 | Kế hoạch | KH | Có |
| 11 | Phương án | PA | Có |
| 12 | Đề án | ĐA | Có |
| 13 | Dự án | DA | Có |
| 14 | Báo cáo | BC | Có |
| 15 | Biên bản | BB | Có |
| 16 | Tờ trình | TTr | Có |
| 17 | Hợp đồng | HĐ | Có |
| 18 | Công văn | (không có) | **Không** |
| 19 | Công điện | CĐ | Có |
| 20 | Bản ghi nhớ | GN | Có |
| 21 | Bản thỏa thuận | TTh | Có |
| 22 | Giấy ủy quyền | GUQ | Có |
| 23 | Giấy mời | GM | Có |
| 24 | Giấy giới thiệu | GGT | Có |
| 25 | Giấy nghỉ phép | GNP | Có |
| 26 | Phiếu gửi | PG | Có |
| 27 | Phiếu chuyển | PC | Có |
| 28 | Phiếu báo | PB | Có |
| 29 | Thư công | (đặc thù) | Có |

**Công văn là loại đặc biệt**: không có tên loại in hoa, trích yếu đặt ở ô 5b (sau "V/v"), ký hiệu kiểu "Số: NN/CQ-ĐV" (vd: "Số: 15/UBND-VP").

## Quy trình nhận diện (chạy theo thứ tự, dừng khi tìm thấy)

### Bước 1: Quét Tên loại (ưu tiên cao nhất)

Tìm paragraph thỏa **tất cả** điều kiện:
- Toàn bộ ký tự là chữ in hoa hoặc khoảng trắng (cho phép có dấu).
- Căn giữa (`<w:jc w:val="center"/>`).
- Độ dài text 2-50 ký tự.
- Không kết thúc bằng dấu chấm câu.
- Vị trí: nằm sau các paragraph của khối Quốc hiệu / Số ký hiệu (tức là không phải ở trên cùng).
- Không phải là Quốc hiệu (text không khớp `CỘNG\s*HO[ÀA]\s+XÃ\s+HỘI`).
- Không phải là tên cơ quan (text không chứa từ điển cơ quan như "BỘ", "UBND", "SỞ", "ỦY BAN", "TỔNG CỤC", "CỤC", "PHÒNG", "BAN", "VIỆN", "TRUNG TÂM" ở đầu).

Đối sánh text (loại bỏ khoảng trắng thừa, normalize) với danh sách 28 tên loại (trừ Công văn). Hỗ trợ:
- Khớp chính xác: "QUYẾT ĐỊNH" → Quyết định.
- Khớp một phần: "QUYẾT ĐỊNH CỦA CHỦ TỊCH" → Quyết định.
- Khớp có dấu/không dấu: "QUYET DINH" → Quyết định (nhưng cảnh báo trong báo cáo).

→ Trả về loại văn bản, độ tin cậy = "cao".

### Bước 2: Quét ký hiệu văn bản

Nếu Bước 1 không thành công, tìm paragraph khớp regex:
```
^\s*Số\s*:\s*\d+\s*/\s*([A-Za-zĐđ]+)(?:\-[A-Za-zĐđ\.]+)?\s*$
```

Capture nhóm chữ viết tắt loại (vd: "QĐ", "TTr", "NQ", "TB", "BC"...). Đối chiếu với cột "Viết tắt" trong bảng 29 loại.

**Trường hợp đặc thù Công văn**: ký hiệu Công văn có dạng "Số: NN/CQ-ĐV" (vd: "Số: 15/UBND-VP", "Số: 234/BNV-VTLTNN"). Cụm sau dấu `/` **không** có viết tắt tên loại (chỉ có tên cơ quan + tên đơn vị soạn thảo, ngăn bởi dấu `-`). Heuristics phân biệt:
- Nếu cụm sau `/` **không** khớp danh sách viết tắt 28 loại trên → **Công văn**.
- Nếu khớp → loại tương ứng.

→ Trả về loại văn bản, độ tin cậy = "trung bình" (vì ký hiệu có thể bị soạn sai).

### Bước 3: Suy luận từ ngữ cảnh

Nếu cả 2 bước trên thất bại, suy luận:
- Có "V/v" ở ô trích yếu → Công văn.
- Có "Kính gửi:" ở phần đầu nội dung (trước Căn cứ) → Tờ trình hoặc Công văn (cần thêm tín hiệu).
- Có "Căn cứ ..." nhiều lần ở đầu nội dung → Quyết định / Chỉ thị / Thông tư.
- Có cụm "BÁO CÁO" trong nội dung tự xưng → Báo cáo.

→ Trả về loại văn bản, độ tin cậy = "thấp".

### Bước 4: Hỏi người dùng

Nếu mọi heuristic thất bại hoặc độ tin cậy "thấp":

> "Tôi không xác định được chắc chắn loại văn bản. [Kết quả suy luận: ...]. Bạn xác nhận giúp đây là loại văn bản gì? Một số loại phổ biến: Công văn, Tờ trình, Quyết định, Báo cáo, Thông báo, Kế hoạch, Nghị quyết, Chỉ thị."

Sau khi người dùng trả lời, lưu vào biến `doc_type` và tiếp tục.

## Tín hiệu phân biệt một số loại dễ nhầm

### Công văn vs Tờ trình
- Cả hai đều có "Kính gửi:" ở đầu phần nội dung.
- Công văn: không có Tên loại, có "V/v" ở trích yếu.
- Tờ trình: có Tên loại "TỜ TRÌNH" in hoa, không có "V/v".

### Quyết định vs Nghị quyết vs Chỉ thị
- Đều có Tên loại + nhiều Căn cứ.
- Quyết định: Tên loại "QUYẾT ĐỊNH", thường có cấu trúc "QUYẾT ĐỊNH: Điều 1. ...".
- Nghị quyết: Tên loại "NGHỊ QUYẾT", thường ban hành bởi tập thể (Hội đồng, Ủy ban Thường vụ).
- Chỉ thị: Tên loại "CHỈ THỊ", văn phong mệnh lệnh, không có cấu trúc Điều.

### Báo cáo vs Tờ trình
- Báo cáo: trình bày kết quả/tình hình, kết cấu Phần/Mục, không xin phê duyệt.
- Tờ trình: trình bày để xin phê duyệt/quyết định, có cụm "kính trình", "đề nghị xem xét".

## Trường hợp đặc biệt: phụ lục văn bản

Nếu file đầu vào bắt đầu bằng "Phụ lục" + số La Mã, in thường đậm, căn giữa → đây là phụ lục của một văn bản khác. Skill vẫn xử lý theo cùng quy định nhưng lưu ý:
- Phụ lục không có Quốc hiệu / Số ký hiệu / Địa danh riêng.
- Đánh số trang riêng theo từng phụ lục (theo Mục III điểm 1đ Phụ lục I NĐ30).
- Thông tin chỉ dẫn "(Kèm theo văn bản số.../...)" đặt ngay dưới tên phụ lục, in thường nghiêng.

→ Flag trong báo cáo: "Đây là phụ lục văn bản. Áp dụng quy định Mục III điểm 1 Phụ lục I NĐ30."
