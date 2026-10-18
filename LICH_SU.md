# Lịch sử hình thành quy trình — các lần sai và bài học cứng

**Agent nào chạy skill này cũng phải đọc hết file này trước khi làm.** Mỗi bài học dưới đây đều có từ một lần làm sai thật: người dùng phải chỉ ra lỗi, hoặc khuôn in ra bị hỏng. Quy tắc trong `SKILL.md` và tham số trong `scripts/khuon3d.py` là kết quả của các lần sửa đó. Đừng "tối ưu" ngược lại.

Mục cuối có danh sách kiểm tra rút gọn. Khi gặp lỗi mới, ghi thêm một đợt vào cuối file theo cùng mẫu: *bối cảnh → sai/thất bại → nguyên nhân → bài học cứng*. Sau đó cập nhật `SKILL.md`/script tương ứng rồi commit.

---

## Đợt 1 — Bộ hoa Poppy (~12–13/10/2026, claude.ai): skill đầu tiên

**Bối cảnh:** bản vẽ bút chì và bút xanh. Mỗi hình có số đo ghi tay, ví dụ "5,5 × 7,5".

| Sai / thất bại | Nguyên nhân | Bài học cứng |
|---|---|---|
| Đọc "5,5 × 7,5" thành 55 × 75 mm (lệch 10 lần) | Người Việt dùng dấu phẩy làm dấu thập phân, đơn vị ghi tay là **cm** | Số ghi tay mặc định là cm, dấu phẩy là dấu thập phân. Nếu kích thước suy ra trông vô lý so với khổ giấy thì phải hỏi lại. |
| Chữ và số viết bằng bút xanh bị lấy lẫn vào viền | Không tách kênh mực | Lọc mực xanh (`b - r > 25`) khỏi mặt nạ viền. Chỉ tắt bộ lọc (`loc_chu_xanh: false`) khi chính viền được vẽ bằng mực xanh. |
| Khuôn to hơn số đo khoảng một độ dày nét | Lấy mép ngoài của nét bút | Đường cắt phải nằm ở **tâm nét**: trừ nửa bề rộng nét (khoảng ±2,5 px). |
| Kích thước lệch sau khi làm trơn spline | Spline làm co hoặc phình bbox | Chỉnh tỷ lệ **2 lần**: làm trơn trước, rồi rescale đúng bbox theo số đo. |
| Khử nhiễu bằng buffer 2,5 / −5 làm mất cuống | Cuống mảnh hơn 5 mm bị buffer âm ăn mất | Chỉ khử nhiễu bằng buffer **1 / −2 / 1**. Không được tăng lên. |
| Cuống bị bo tròn, mất góc | Spline làm mượt góc | Tăng trọng số điểm góc ở cuống (×13). |
| Mép lưỡi 1,0 mm được ghi là "chuẩn" (AGSMem #26997) | Đúng cho bộ Poppy, nhưng các bộ sau người dùng muốn **0,5 mm** | Mép lưỡi mặc định hiện là 0,5 mm. Số "chuẩn" nào cũng chỉ đúng cho bộ đó. Người dùng nói số khác thì theo người dùng. |

---

## Đợt 2 — Chân ngỗng từ ảnh chụp màn hình CAD (15–16/10/2026, task 20984)

**Bối cảnh:** chỉ có ảnh chụp màn hình phần mềm CAD đang đo bản vẽ (`IMG_20261015_095706.jpg`). Ảnh phải xoay 180°, độ phân giải thấp (762 × 610, khoảng 3,9 px/mm). Người dùng yêu cầu mép 0,5 mm.

| Sai / thất bại | Nguyên nhân | Bài học cứng |
|---|---|---|
| Lớp phủ CAD lọt vào viền: ô chữ xám bán trong suốt đè lên nét, đường kích thước, trục đỏ/xanh, vòng con trỏ | Ảnh nguồn không sạch | Ảnh có lớp phủ CAD hoặc chú thích đè lên nét thì **xin bản scan gốc trước**. Chỉ tự làm sạch khi người dùng không có bản khác, và phải báo rõ chỗ nào là nét đoán. |
| Phải tự nối nét bị ô chữ che. Nét nối là phỏng đoán | Thông tin gốc bị che | Vẽ nét đoán thành nét đứt trong ảnh đối chiếu để người dùng nhìn ra. |
| Phép opening 3×3 làm đứt nét lá | Nét quá mảnh ở độ phân giải thấp | Ở ảnh dưới khoảng 5 px/mm không dùng opening trước khi nối nét. |
| close 13 lấp khe giữa các thuỳ ở lá 7 | Phép đóng lớn nối hai mép khe | Đây là dấu hiệu sớm của lỗi khe. Bài học cuối cùng nằm ở đợt 5. |
| Lá 6 mất mũi thuỳ ở chỗ xoá đường trục. Đáy lá 7 tràn ra mép box do vạch kích thước | Xoá lớp phủ đã xoá luôn nét thật, vạch đo dính vào viền | Sau khi làm sạch phải soi **từng** hình ở mức phóng to, nhất là chỗ đường phủ cắt qua nét. |
| Chữ trong ảnh render bị lỗi trên Windows | Không có font DejaVu | Script tự chọn font có sẵn (arial trên Windows). Đường dẫn Unicode phải đọc qua `np.fromfile` + `cv2.imdecode`. |
| Agent dừng lại để hỏi khi đang chạy việc do agent khác giao | Làm sai luật giao việc | Việc giao giữa các agent thì **không hỏi**. Ghi điều cần hỏi vào `task log` / `done`, rồi làm theo cách an toàn nhất. |
| Kết quả chỉ nằm trên máy | Thiếu bước giao | Mọi kết quả hoa đất sét phải gửi vào nhóm Zalo **Trạm Test** và tag **chị Nhi Hoa Đất**. |

---

## Đợt 3 — Codex #50765: "BẮT BUỘC CHẠY SKILL … ĐỂ LÀM KỸ" (16/10/2026 sáng)

| Sai / thất bại | Nguyên nhân | Bài học cứng |
|---|---|---|
| Agent không tìm thấy skill trong thư mục AGS, phải dùng script cũ chép trong "Phụ lục A" của bản đồng bộ claude.ai | Skill nằm rải nhiều nơi, các bản lệch nhau | **Chỉ có một bản chuẩn**: repo GitHub `goccontent/lam-khuon-cat-3d`. Bản đồng bộ trên claude.ai chỉ mới khi tải zip lên lại. Script nằm ở `scripts/`, không nhúng vào SKILL.md. |
| Dùng mép 1 mm trong khi người dùng đã yêu cầu 0,5 mm | Lấy số "chuẩn" cũ thay vì yêu cầu hiện tại | **Yêu cầu trong prompt hiện tại thắng mọi mặc định và mọi ghi nhớ cũ.** Trước khi dựng, đọc lại prompt và đối chiếu từng thông số. |
| Phép đóng mặc định làm mất các khe sâu của lá. Agent phải tự mò ngưỡng | Cách lấy viền `outer` + close lớn | Xem đợt 5. |
| Nét bị đứt ở cánh vừa lớn và lá lớn | Ảnh mờ | Nối nét đứt có kiểm soát (`bridge`), rồi soi lại đúng chỗ đã nối. |
| Nạp lại STL thì 2 file (2, 7) có tam giác suy biến | Xuất STL dùng float32 nên đỉnh sát nhau bị gộp | **Luôn nạp lại STL sau khi xuất và kiểm tra kín khối.** Không tin kết quả kiểm tra trên mesh trong bộ nhớ. |

## Đợt 4 — Codex #50829 và #5087a: người dùng bắt vẽ lại viền (16/10/2026)

- #50829, người dùng nói: *"Các đường viền đỏ bạn vẽ lại chưa được đúng theo nét bản gốc. Vẽ lại đi."*
- #5087a, người dùng nói: *"Vẽ lại viền lá lớn đi, tôi thấy nét đỏ bạn vẽ và nét chì bản gốc có nhiều chỗ chưa trùng nhau. Làm thật kỹ."*

| Sai / thất bại | Nguyên nhân | Bài học cứng |
|---|---|---|
| Viền bo tròn mất răng cưa và khe. Lá lớn mất một khe sâu | Làm trơn hoặc đóng quá tay. Agent chỉ nhìn ảnh thu nhỏ rồi báo "khớp" | **Soi ở mức phóng to (≥ 4×, chỗ khó thì 8×)** từng răng, từng khe, từng cuống, với viền chồng lên nét gốc. Không báo "khớp" khi mới nhìn ảnh tổng. |
| Răng trái lá lớn đặt quá thấp. Có móc và góc bị cắt | Lỗi chỉ thấy khi phóng to | Có công cụ soi (`soi`, ảnh `soi/<id>.jpg`) và ảnh đối chiếu 2D. Phải tự xem từng ảnh trước khi gửi. |
| Người dùng phải chỉ lỗi 2 lần liền | Agent sửa cả bộ một lượt, không cho duyệt từng bước | Khi người dùng chỉ ra chỗ sai: **sửa một khuôn trước**, gửi ảnh phóng to vùng đó để duyệt, rồi mới áp cho các khuôn còn lại. |

---

## Đợt 5 — Chân ngỗng A4 bản scan nét (16/10/2026 chiều, #519e5 / #51abe)

Người dùng nói: *"Nhớ soi kỹ các viền. Và lưu ý để mép thành 0,5mm"*. Sau đó gửi ảnh scan mới `20261016_160408.jpg` và hỏi: *"Đo xem có phải nó được vẽ trên giấy khổ A4 không"*.

| Sai / thất bại | Nguyên nhân | Bài học cứng |
|---|---|---|
| File PDF trên Drive có 0 byte | Lỗi lúc tải lên | Kiểm tra dung lượng file trước. Nếu rỗng thì báo ngay và nhờ tải lại, không đoán. |
| Bản vẽ không ghi số đo | — | Lấy tỷ lệ theo khổ giấy: A4 thì tỷ lệ cạnh phải ≈ 1,4142 và bốn mép ảnh đều là giấy, `px/mm = rộng_px / 210`. Báo độ lệch tỷ lệ và báo rằng kích thước đã làm tròn 0,5 mm. |
| "Mép thành 0,5 mm" dễ hiểu nhầm là cả thân dày 0,5 mm | Câu chữ mơ hồ | Hiểu là **mép lưỡi** 0,5 mm, thân vẫn 1,5 mm và vát dần. Phải nói rõ cách hiểu này với người dùng, vì thân 0,5 mm sẽ gãy. |
| Người dùng nói *"Lá vừa thấy có vẻ sai sai"*, rồi chọn trong form: "Khe giữa các thuỳ bị lấp đặc / cạn quá" | Cách `outer` + close 13: cuối khe hai mép nét chập thành một, phép đóng lấp mất tới khoảng 8 mm khe. close nhỏ (3) thì viền lọt qua chỗ nét đứt. Chỉ lấy lòng trong thì cụt mũi răng, chỉ lấy mép ngoài thì cụt khe | Mặc định là contour **`trong`**: nối nét (`bridge` 4), loang nền lấy lòng trong, rồi kết hợp với mép ngoài trừ vùng khe (`slit_k` 21). Không quay lại `outer` cho lá xẻ thuỳ. |
| Một vết bẩn xám trên đỉnh lá lớn cắt mất một răng | Vết bẩn bị tính là nét | Cách `trong` xử lý được lỗi này. Vẫn phải soi đỉnh lá. |
| Báo "kín khối = True" nhưng nạp lại STL thì 4/7 file không kín (cạnh không-manifold ở đáy đế z = 0) | Kiểm tra trên mesh trong bộ nhớ. float32 gộp các đỉnh sát nhau | Polygon dùng `simplify(0.005)` + `set_precision(0.001)`. Script **bắt buộc nạp lại từng STL** để kiểm tra kín khối và kích thước lòng khuôn. Lỗi thì dừng, không giao. |
| Khe hẹp dưới 3 mm vẫn bị thân 1,5 mm lấp thành khối đặc ở mặt ngoài | Thân hai thuỳ chạm nhau | Đã hỏi người dùng các phương án. Chốt ở đợt 6. |
| Agent tự sửa script trong thư mục `out_*` | Không có quy trình đưa bài học về skill | Bài học mới phải đưa vào **repo skill** (SKILL.md + script). Không để nằm rải ở thư mục làm việc. |

---

## Đợt 6 — Chuẩn hoá và đóng gói skill (18/10/2026)

| Sai / thất bại | Nguyên nhân | Bài học cứng |
|---|---|---|
| Khe hẹp bị lấp đặc (tồn từ đợt 5) | — | Người dùng chọn **thân 0,8 mm riêng vùng khe** (`wall_khe` 0,8, mặc định cho mọi lá). Vùng khe được tìm bằng phép opening phần bù bên ngoài, lọc diện tích ≥ 0,3 mm². Khe dưới khoảng 1,6 mm vẫn còn đặc một đoạn sát đỉnh, đây là bình thường. Khi giao, gửi kèm ảnh so sánh khe. |
| Báo cáo cuối cho người dùng viết bằng tiếng Anh | Sơ suất | Luôn trả lời bằng **tiếng Việt**, xưng "mình". |
| Hỏi lại "đóng gói" nghĩa là gì | — | Với người dùng này, "đóng gói skill" nghĩa là đẩy lên GitHub, có link là đủ. |
| (Yêu cầu mới) | Agent sau dễ lặp lại lỗi cũ vì không biết lịch sử | **Luật bắt buộc khi đóng skill:** phải có file lịch sử này, gồm các lần sai/thất bại và bài học cứng. Mỗi lần sửa skill thì ghi thêm đợt mới. |

---

## Danh sách kiểm tra rút gọn (đọc trước mỗi lần chạy)

1. Lấy được file gốc và dung lượng lớn hơn 0. Có lớp phủ CAD hoặc chú thích đè nét thì xin bản sạch.
2. Thông số theo **prompt hiện tại** (mép, thân, chiều cao), không theo số "chuẩn" cũ.
3. Tỷ lệ: số ghi tay là cm, dấu phẩy là thập phân. Không ghi số thì lấy theo khổ giấy (A4 = 210 × 297) và kiểm tra tỷ lệ cạnh.
4. Viền nằm ở tâm nét. Dùng contour `trong` cho lá xẻ thuỳ. Khử nhiễu không vượt quá buffer 1 / −2 / 1.
5. Soi từng hình ở mức phóng to: răng, khe, cuống, chỗ nét đứt. Không báo "khớp" khi mới nhìn ảnh tổng.
6. Khe hẹp dùng `wall_khe` 0,8. Mép lưỡi vát xuống 0,5 mm.
7. Nạp lại **từng** STL: kín khối và lòng khuôn đúng kích thước. Lỗi thì không giao.
8. Người dùng chỉ lỗi thì sửa một khuôn trước, gửi ảnh phóng to để duyệt, rồi mới làm cả bộ.
9. Giao bằng tiếng Việt, gửi Zalo Trạm Test và tag chị Nhi. Hỏi người dùng bằng form (trong AGS), không hỏi trong terminal.
10. Bài học mới đưa vào repo skill và ghi thêm một đợt vào file này.
