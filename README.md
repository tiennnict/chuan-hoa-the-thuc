# chuan-hoa-the-thuc

**Skill cho Claude.ai** — Chuẩn hóa thể thức và kỹ thuật trình bày văn bản hành chính Việt Nam theo Nghị định số 30/2020/NĐ-CP.

---

## Tổng quan

Skill này hướng dẫn Claude thực hiện tự động quy trình chuẩn hóa văn bản hành chính theo đúng quy định của Nghị định 30/2020/NĐ-CP và các Phụ lục kèm theo. Người dùng chỉ cần upload file `.docx` hoặc `.doc`, Claude sẽ trả về bản đã chuẩn hóa cùng báo cáo thay đổi chi tiết.

**Đầu vào:** File `.docx` / `.doc` chứa văn bản hành chính.  
**Đầu ra:** File `*_chuanhoa.docx` + báo cáo `*_baocao.md`.

---

## Tính năng

- Nhận diện tự động 29 loại văn bản hành chính (Công văn, Quyết định, Tờ trình, Báo cáo, Thông báo, Kế hoạch, Nghị quyết, Chỉ thị...).
- Sửa lỗi gõ máy phổ biến: khoảng trắng thừa, dấu thanh sai vị trí, lỗi telex còn sót, lỗi chính tả theo từ điển.
- Áp quy tắc viết hoa theo Phụ lục II Nghị định 30.
- Chuẩn hóa styles (Normal, Heading 1–5, Title, CanCu, NoiNhanLabel, NoiNhanItem, KhoanCoTieuDe).
- Chuẩn hóa page setup (khổ A4, lề theo quy định) cho mọi section, kể cả landscape.
- Thêm header số trang đúng chuẩn, áp dụng cho mọi section.
- Kiểm tra bảng cụm (Quốc hiệu + Tên cơ quan; Nơi nhận + Chân ký): đảm bảo viền trong suốt, không vượt content margin.
- Flag các thành phần thiếu hoặc sai vị trí (không tự thêm).
- Gợi ý hành văn: câu rườm rà, từ không chuẩn mực, mệnh đề có thể gây hiểu nhầm pháp lý (không tự sửa).

---

## Giới hạn áp dụng

Skill này **chỉ áp dụng** cho văn bản hành chính của cơ quan nhà nước thuộc phạm vi Nghị định 30/2020/NĐ-CP.

**Không dùng** cho:
- Hợp đồng, văn bản thương mại tư nhân.
- Sách, báo, tài liệu nghiên cứu.

---

## Cài đặt vào Claude.ai

1. Clone hoặc tải repository này về máy.
2. Truy cập **Claude.ai > Settings > Skills** (hoặc cơ chế tương đương tùy phiên bản).
3. Trỏ đường dẫn đến file `SKILL.md` trong thư mục này.
4. Claude sẽ tự động nhận diện và kích hoạt skill khi người dùng đề cập đến chuẩn hóa văn bản hành chính.

> Lưu ý: Cơ chế cài đặt skill có thể thay đổi theo phiên bản Claude.ai. Tham khảo tài liệu chính thức của Anthropic nếu cần.

---

## Cấu trúc thư mục

```
chuan-hoa-the-thuc/
├── SKILL.md                          # File skill chính — Claude đọc file này
├── references/
│   ├── phuluc1-the-thuc.md           # Quy định thể thức chi tiết (Phụ lục I)
│   ├── phuluc2-viet-hoa.md           # Quy tắc viết hoa (Phụ lục II)
│   ├── chuan-ky-thuat.md             # Bảng tham số kỹ thuật, styles XML, header XML
│   ├── nhan-dien-loai-van-ban.md     # Heuristics + danh sách 29 loại văn bản
│   ├── loi-go-may.md                 # Danh sách lỗi gõ máy + regex
│   └── template-bao-cao.md           # Template cố định cho báo cáo đầu ra
├── scripts/
│   ├── normalize.py                  # Script xử lý chính (Phase 1–7 + report)
│   └── data/
│       └── typo_dict.json            # Từ điển lỗi chính tả
├── tests/
│   ├── inputs/                       # File mẫu đầu vào (không commit tài liệu thật)
│   └── expected/                     # Kết quả mong đợi để so sánh
├── .gitignore
├── LICENSE
└── README.md
```

---

## Quy trình xử lý tổng quan

Skill thực hiện 8 giai đoạn tuần tự, không đảo thứ tự:

| Giai đoạn | Nội dung |
|-----------|----------|
| 1 | Chuẩn bị file đầu vào (convert `.doc` → `.docx` nếu cần) |
| 2 | Unpack XML |
| 3 | Nhận diện loại văn bản + xác định cặp cỡ chữ (13pt hoặc 14pt) |
| 4 | Phase 1: Sửa lỗi gõ máy + viết hoa |
| 5 | Phase 2: Phân loại paragraph (component classification) |
| 6 | Phase 3: Chuẩn hóa Styles + áp formatting |
| 7 | Phase 4–5: Chuẩn hóa Page Setup + Header số trang |
| 8 | Phase 6–7: Kiểm tra bảng cụm + Flag + Gợi ý hành văn |
| 9 | Pack lại, validate, sinh báo cáo, trả kết quả |

---

## Nguyên tắc xử lý

- **Không tự thêm thành phần thiếu.** Chỉ flag để người dùng tự quyết.
- **Không tự sửa hành văn.** Chỉ gợi ý trong báo cáo.
- **Graceful degradation:** Nếu một phase lỗi, ghi vào báo cáo và tiếp tục các phase sau, miễn output cuối validate được.
- Validate sau pack: thử lại tối đa 2 lần trước khi báo lỗi cho người dùng.

---

## Đóng góp

Mọi đóng góp đều được hoan nghênh, đặc biệt:
- Cập nhật `typo_dict.json` với các lỗi gõ máy phổ biến mới.
- Bổ sung heuristics nhận diện loại văn bản trong `nhan-dien-loai-van-ban.md`.
- Báo cáo edge case qua Issues.

Vui lòng mở **Issue** trước khi tạo **Pull Request** với thay đổi lớn.

---

## Giấy phép

Nội dung trong repository này được phát hành theo giấy phép [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).

Bạn được tự do sử dụng, chỉnh sửa và phân phối lại — với điều kiện ghi rõ nguồn gốc.
