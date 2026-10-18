---
name: "lam-khuon-cat-3d"
description: "Làm khuôn cắt 3D (cookie/clay cutter) từ bản vẽ hoặc bản scan hình cánh hoa, lá: tách đường viền (giữ khe xẻ thuỳ, mũi răng, nét cuống), chỉnh đúng số đo ghi tay hoặc tỷ lệ khổ giấy, dựng STL kín khối có vát mép, render ảnh xem trước và ảnh đối chiếu 2D. Dùng khi người dùng gửi bản vẽ/scan và nói làm khuôn, khuôn cắt, khuôn 3D, cutter, file STL để in."
---

# Làm khuôn cắt 3D từ bản vẽ scan

Dùng khi người dùng gửi ảnh chụp hoặc bản scan (JPG/PNG/PDF) một tờ giấy có vẽ các hình (cánh hoa, lá…), kèm hoặc không kèm số đo ghi tay, và muốn có khuôn cắt 3D (cookie/clay cutter) để in.

Trả lời bằng tiếng Việt, xưng "mình". Người dùng đọc trên điện thoại, nên câu trả lời ngắn và đưa kết quả trước.

Toàn bộ quy trình đã kiểm chứng nằm trong `scripts/khuon3d.py` (cùng thư mục với file này). **Không viết lại thuật toán**: các tham số trong script đã được người dùng duyệt qua nhiều vòng sửa. Nếu phải sửa script cho một bộ khuôn, sửa trong bản sao ở thư mục làm việc, rồi báo lại để đưa vào skill.

**BẮT BUỘC đọc `LICH_SU.md` trước khi làm**: file đó ghi lịch sử hình thành quy trình, gồm từng lần làm sai hoặc thất bại và bài học cứng rút ra. Phần lớn lỗi một agent mới có thể mắc đã xảy ra ở đó. Khi sửa skill này, ghi thêm một đợt vào cuối `LICH_SU.md`.

Agent chạy skill này cần: chạy được Python 3 và cài thư viện, **xem được ảnh** (để soát viền), và có cách giao file/hỏi người dùng (xem mục 6).

---

## 0. Trước khi làm

1. **Lấy được file gốc.** Link Drive có thể trả file **0 byte** (tải lên bị lỗi). Kiểm tra dung lượng; nếu rỗng thì báo ngay và nhờ tải lại, đừng đoán.
2. **Đọc số đo trên bản vẽ.** Người dùng thường ghi `W x H mm` cạnh từng hình. W là chiều ngang, H là chiều dọc của chính đường viền hình, đúng thứ tự người dùng ghi. Khi mỗi hình có số ghi riêng, chỉnh **riêng** từng hình về đúng số ghi của nó; không dùng một tỷ lệ chung cho cả tờ.
3. **Soát số ghi sai.** Ví dụ thực tế: người dùng ghi "5,5 × 7,5 mm" cho chiếc lá cao gần bằng các hình 60–75 mm khác.
   - Đây là lỗi dấu phẩy, số đúng là **55 × 75 mm**.
   - Bước `extract` tự đánh dấu "NGHI SỐ GHI SAI" khi px/mm của một hình lệch quá 1,6 lần so với trung vị cả tờ.
   - Cứ làm theo cách hiểu hợp lý nhất, rồi **nói rõ** cách hiểu đó trong câu trả lời.
4. **Không có số đo nào** → tìm tỷ lệ theo thứ tự:
   1. **Khổ giấy.** Nếu ứng dụng scan đã cắt sát mép giấy (bốn mép ảnh đều là giấy, không thấy mặt bàn), so tỉ lệ ảnh với khổ giấy: A4 = 210 × 297 mm, tỉ lệ 1,4142. Lệch dưới 0,5% thì px/mm = rộng_px / 210 (kiểm lại bằng cao_px / 297). Ví dụ bộ chân ngỗng: ảnh 2439 × 3447 px, lệch 0,07%, ra 11,61 px/mm.
   2. **ppi của bản scan PDF** (`pdfimages -list`).
   3. Hỏi một số đo thật của một hình làm chuẩn.
   - Khi đó **mọi hình dùng chung một tỷ lệ**. Chạy `extract` với W, H tạm, lấy `w_px`, `h_px` trong `bao_cao_ty_le.json`, rồi điền W = w_px / px_per_mm, H = h_px / px_per_mm (làm tròn 0,5 mm) và chạy lại `extract` + `build`.
   - Nói rõ tỷ lệ lấy từ đâu và số làm tròn có thể lệch tới 0,25 mm mỗi chiều.
   - Nếu px/mm theo chiều ngang và dọc của hình chuẩn lệch nhau quá khoảng 2%, báo người dùng.
5. **Chất lượng ảnh.**
   - Ảnh dưới khoảng 6 px/mm (ảnh chụp nhỏ, ảnh qua Zalo) cho viền kém sắc. Vẫn làm được nhưng báo người dùng và xin bản scan gốc nếu có.
   - Ảnh chụp màn hình CAD có lớp đo (hộp chữ, đường gióng, trục màu, con trỏ) đè lên nét vẽ phải xoá tay từng chỗ và nối nét bị che bằng phỏng đoán. **Xin bản scan sạch trước**; chỉ làm trên ảnh CAD khi người dùng bảo, và liệt kê các chỗ đã nối phỏng đoán.
   - PDF scan có thể bị xoay 180°: chỉ xoay, không lật.
6. **Hình lồng nhau** (một hình vẽ bên trong hình khác, có số đo riêng, ví dụ cánh nhỏ 43×32 có viền trong 32×20): làm **cả hai** khuôn. Khuôn viền trong đặt id có hậu tố `b` (ví dụ `3b_canh_trong`) và `"contour": "hole"`. Ghi chú rằng người dùng có thể bỏ khuôn này nếu đó chỉ là nét phụ.
7. **Ảnh khuôn mẫu:** nếu người dùng gửi ảnh khuôn mẫu, bám theo kiểu dáng đó và chỉnh các khoá `cutter` cho khớp.
8. **Hỏi tiêu chí "đạt"** khi bắt đầu một việc mới, trong cùng một câu hỏi gộp. Nếu người dùng đã gửi bản vẽ kèm số đo và bảo "làm theo kích thước tôi ghi", coi như đã có tiêu chí: lòng khuôn đúng số ghi, đường viền đúng nét vẽ. Làm luôn, không hỏi lại.

## 1. Thông số khuôn mặc định (người dùng đã duyệt)

| Thông số | Giá trị | Khoá trong `cutter` |
|---|---|---|
| Chiều cao lưỡi | 12 mm | `blade_h` |
| Thân thành | 1,5 mm | `wall` |
| Mép lưỡi cắt | **0,5 mm**, vát dần trong 3 mm trên cùng (12 lát, mỗi lát 0,25 mm) | `edge`, `bevel_h` |
| Đế viền | rộng 4 mm tính từ mặt ngoài thân, dày 2,5 mm | `base_w`, `base_t` |
| Thân trong khe hẹp | 0,8 mm, chỉ ở khe hẹp hơn 2 × thân (mục 4.9) | `wall_khe` |
| Mặt trong lưỡi | thẳng đứng, trùng đường viền hình | (cố định) |

- Mép cắt 0,5 mm là yêu cầu của người dùng từ tháng 10/2026 (bộ Poppy cũ dùng 1,0 mm).
- Người dùng nói "mép thành 0,5 mm" nghĩa là **mép lưỡi** `edge`; thân `wall` vẫn 1,5 mm. Thân 0,5 mm rất dễ gãy khi in, nên nếu họ thật sự muốn thân mỏng thì phải cảnh báo.
- Mặt trong trùng đường viền, nên **kích thước lòng khuôn = kích thước miếng cắt ra = số người dùng ghi**. Kích thước ngoài của khuôn bằng số ghi cộng 11 mm mỗi chiều: (1,5 + 4) × 2.

## 2. Quy trình chạy (đúng thứ tự)

`K` = thư mục chứa `khuon3d.py`. Trên Windows gõ `python` thay cho `python3`; nếu chữ tiếng Việt in ra lỗi thì đặt `PYTHONIOENCODING=utf-8`.

```bash
pip install -r $K/requirements.txt
# PDF: pdfimages -list f.pdf ; pdfimages -png f.pdf raw   (không có poppler: pip install pymupdf rồi xuất ảnh trang)
python3 $K/khuon3d.py grid ANH.jpg OUT        # 1. ảnh lưới toạ độ pixel của ẢNH GỐC
# 2. viết OUT/config.json (mục 3)
python3 $K/khuon3d.py extract config.json     # 3. tách viền + báo cáo px/mm
python3 $K/khuon3d.py soi config.json         # 4. OUT/soi/<id>.jpg: từng hình phóng to + viền đỏ
# 5. SOÁT KỸ: OUT/kiem_tra_vien.jpg (mỗi hình đúng 1 viền đỏ) và TỪNG ảnh OUT/soi/<id>.jpg
python3 $K/khuon3d.py build config.json       # 6. STL + ảnh 3D + ảnh đối chiếu 2D + zip (~1,5–4 phút cho 7 khuôn)
# 7. XEM OUT/doi_chieu_*_2D.png và OUT/tong_hop.png trước khi gửi
```

**Soát viền (bước 5) là bắt buộc** — người dùng dặn "soi kỹ các viền". Với từng ảnh `soi/<id>.jpg` kiểm:
- khe xẻ thuỳ: viền đỏ ăn tới tận đáy khe, không bị cụt;
- mũi răng, mũi thuỳ: nhọn, không bị bo cụt;
- chỗ nét đứt: viền không lọt vào trong hình;
- vết bẩn, nét phác, chữ: không bị viền ôm vào hay cắt mất răng;
- cuống: đúng gờ, đúng góc.

**Chọn khung crop (`box`)**: dùng toạ độ pixel của ảnh gốc, không phải của ảnh thu nhỏ đang xem.
- Ảnh hiển thị cho agent thường bị thu nhỏ. Nhân toạ độ ước lượng với `rong_anh_goc / rong_anh_hien_thi` (ví dụ 1841/1429 = 1,288).
- Khung phải chứa trọn hình, kể cả mũi lá và cuống, và **tránh** chữ ghi số đo.
- Chữ bút bi xanh được tự lọc (b − r > 25). Nếu chính nét viền có lẫn mực xanh (và trên giấy không có chữ xanh) thì đặt `"loc_chu_xanh": false`. Chữ bút chì hoặc mực đen thì không lọc được, phải để ngoài box.
- Hai hình lồng nhau dùng **cùng một box**.

## 3. config.json

Khoá cấp trên: `image`, `out`, `set_name` (tên zip), `shapes`, `cutter` (chỉ ghi khoá muốn đổi so với mục 1), `loc_chu_xanh` (mặc định `true`).

Khoá cho từng hình:

| Khoá | Ý nghĩa | Mặc định |
|---|---|---|
| `id` | tên file: `khuon_<id>.stl`. Đánh số theo thứ tự trên giấy: trái→phải, trên→dưới | bắt buộc |
| `name` | tên tiếng Việt in trên ảnh | bắt buộc |
| `box` | `[x0,y0,x1,y1]` pixel ảnh gốc | bắt buộc |
| `W`, `H` | số đo (mm) | bắt buộc |
| `kind` | `petal` (cánh, đường cong trơn) hoặc `leaf` (lá răng cưa, xẻ thuỳ) | bắt buộc |
| `contour` | `trong` · `outer` · `hole` (xem dưới) | **trong** |
| `thresh` | ngưỡng nét: **30** cho bút mực hoặc chì đậm, **16** cho nét bút chì mờ | 30 |
| `bridge` | (`trong`) bán kính nối chỗ nét đứt, px | 4 |
| `slit_k` | (`trong`) cỡ nhận diện khe, px; khe rộng hơn mà vẫn bị lấp thì tăng | 21 |
| `close` | nhân đóng nét, px. `trong` không cần (1); `outer` dùng 13 | 1 / 13 |
| `hole_rank` | (`hole`) thứ hạng lỗ theo diện tích. Lỗ 0 thường là vành giữa hai viền; **lỗ 1 là lòng viền trong** | 1 |
| `stem_x_frac` | vị trí ngang của cuống theo tỉ lệ W. Chỉ đặt khi cuống **không** phải điểm thấp nhất của hình (ví dụ cánh lớn Poppy: 0,47) | tự lấy điểm thấp nhất |
| `smooth` | hệ số làm mượt spline | petal 0,02 · leaf 0,003 |
| `stroke_half_px` | (`outer`/`hole`) nửa bề dày nét bút (px) | 2,5 |

**Ba cách lấy viền:**
- `trong` (mặc định, từ bộ chân ngỗng 16/10/2026): nối nét đứt ≤ 2×`bridge` px → tô loang lấy lòng trong của nét → cộng phần mép ngoài **chỉ ở chỗ lồi** (mũi răng) → đưa về tâm nét. Khe xẻ thuỳ giữ đúng tới đáy, mũi răng vẫn nhọn. Với cánh hoa trơn, kết quả lệch cách cũ dưới 0,13 mm, nên dùng cho cả bộ.
- `outer`: mép ngoài nét + close 13, co vào 2,5 px. Lỗi đã biết: ở cuối khe hẹp hai mép vẽ chập thành một nét nên khe bị lấp, có chỗ cụt tới ~8 mm. Chỉ dùng khi `trong` hỏng (ví dụ nét đứt quá rộng, tô loang tràn vào trong hình).
- `hole`: viền trong của hình lồng, nở ra 2,5 px.

Config mẫu đã duyệt nằm ở **Phụ lục**.

## 4. Những điểm bắt buộc giữ (bài học từ các lần sửa)

1. **Cuống phải đúng nét vẽ.** Đây là lỗi người dùng đã bắt sửa.
   - Cuống cánh hoa và cuống lá thường là một gờ **đầu bằng, có góc**, đôi khi có mũi nhọn lệch một bên.
   - Làm mượt đều toàn hình sẽ bo tròn mất gờ này. Vì vậy script:
     - khử nhiễu nhẹ `buffer(1).buffer(-2).buffer(1)`, **không** dùng `2.5/-5/2.5`;
     - đặt trọng số spline cao gấp 13 lần ở vùng cuống (Gauss bán kính 7 mm với cánh, 5 mm với lá; chỉ tính phần thấp hơn 8–10 mm tính từ đáy);
     - lấy mẫu dày 0,15 mm.
   - Kiểm tra ở khung "cuống (lưới 1 mm)" trong `doi_chieu_*_2D.png`: nét hồng phải nằm trong nét xám, lệch dưới 0,3 mm.
   - Nếu cuống không phải điểm thấp nhất (khung phóng to không thấy cuống), đặt `stem_x_frac`.
2. **Khe xẻ thuỳ phải ăn tới đáy.** Dùng `contour: "trong"` (mặc định) và soát bằng `soi/<id>.jpg`. Đây là lỗi người dùng đã bắt sửa ở bộ chân ngỗng.
3. **Tâm nét bút.** Viền khuôn luôn đi theo **tâm** nét vẽ; script tự xử lý theo từng cách lấy viền. Sau đó mới chỉnh về W×H.
4. **Hệ trục.** Ảnh có y hướng xuống, CAD có y hướng lên, nên lật bằng `scale(1,-1)`. Việc lật chỉ đổi hệ trục; nhìn từ trên xuống, hình vẫn giống bản vẽ.
5. **Chỉnh kích thước 2 lần.** Chỉnh bbox về W×H trước khi làm mượt, và chỉnh lại lần nữa sau khi làm mượt. Lòng khuôn phải ra **đúng 2 chữ số thập phân**, ví dụ `64.00 x 39.00`.
6. **Lệch tỷ lệ.** Nếu báo cáo ghi "lệch tỷ lệ > 5%", hình sẽ bị co hoặc giãn một chiều để khớp số ghi.
   - Vẫn làm theo số ghi.
   - Báo người dùng hình nào lệch, lệch bao nhiêu phần trăm.
   - Đề nghị phương án giữ đúng dáng vẽ: chỉ khớp một chiều, chiều kia theo tỷ lệ bản vẽ.
7. **Kín khối sau khi nạp lại STL.** Lúc dựng báo kín chưa đủ: STL lưu toạ độ float32, các đỉnh quá sát nhau ở đáy đế bị gộp và làm hở khối (đã gặp ở 4/7 khuôn chân ngỗng). Script đã làm sạch viền (`simplify 0.005` + `set_precision 0.001`, lệch ≤ 0,003 mm) và **nạp lại từng STL để kiểm**. Thấy dòng `!!! STL NẠP LẠI KHÔNG KÍN KHỐI` hoặc `kín khối=False` thì chưa được gửi; kiểm tra lại contour (thường do box cắt ngang hình hoặc ngưỡng quá thấp).
8. **Cuống quá hẹp.** Nếu lòng cuống hẹp dưới khoảng 2 mm (ví dụ lá xẻ thuỳ Poppy chỉ 1 mm), giữ đúng nét vẽ nhưng **cảnh báo** người dùng rằng phôi đất sét dễ kẹt, và đề nghị nới ra khoảng 2 mm.
9. **Khe hẹp hơn 2 × thân (3 mm) bị đặc phía ngoài.** Thân 1,5 mm của hai thuỳ dính nhau, nên nhìn khuôn thấy khe bị "lấp", dù đường cắt bên trong vẫn đúng tới đáy khe. Mặc định đã xử lý: `wall_khe` = 0,8 mm. Hàm `slit_zone` tìm các khe hẹp hơn 2 × `wall` phía ngoài hình (phép mở hình trên nền ngoài, bỏ vùng < 0,3 mm²); **chỉ trong vùng đó** thân mỏng còn 0,8 mm, ở chỗ khác vẫn 1,5 mm. Phần vát mép không đổi. Đế viền vẫn đặc (nằm dưới, cách mép cắt 9,5 mm).
   - Người dùng chốt 0,8 mm ở bộ chân ngỗng (18/10/2026), áp cho cả lá vừa, lá lớn, lá nhỏ. Cánh hoa không có khe nên không đổi.
   - Đoạn khe hẹp dưới 1,6 mm (sát đáy) vẫn đặc; đó là giới hạn của thân 0,8 mm.
   - Muốn tắt: `"cutter": {"wall_khe": null}`. Muốn đổi độ dày: `"wall_khe": 1.0`.
   - Khi giao bộ có lá xẻ thuỳ, kèm ảnh so sánh thân nhìn từ trên xuống (tím = thân, đỏ = đường cắt) để người dùng thấy khe đã mở.
10. **Nét phụ trong lá** (gân lá, nét phác chì): script chỉ lấy viền ngoài lớn nhất nên tự bỏ qua. Không cần xử lý thêm.
11. **Đừng tự ý đổi** thông số khuôn, màu render hay tên file khi người dùng chưa yêu cầu.
12. **Người dùng đổi thông số khuôn** (thành, mép, chiều cao, đế): sửa `cutter` trong config rồi dựng lại **cả bộ**, để các khuôn luôn đồng bộ.

## 5. Ảnh xem trước (script tự làm)

- `xem_<id>.png`: ảnh 900×780 nhìn nghiêng.
  - Cánh hoa: camera đặt ở (0, −250, 235), xoay hình −8°, cuống quay về phía người xem.
  - Lá: camera ở (0, −230, 260), không xoay.
  - Tiêu đề "Tên — W × H mm", dòng chân ghi thông số khuôn.
  - Nền (236, 237, 240), khuôn màu hồng tím (200, 150, 184), mặt vát màu (232, 200, 222).
- `tong_hop.png`: lưới 3 cột gồm tất cả khuôn.
- `doi_chieu_canh_2D.png` và `doi_chieu_la_2D.png`: mỗi hình có toàn hình và khung phóng to cuống trên lưới 1 mm. Nét xám là bản vẽ gốc, nét hồng là khuôn.
- `soi/<id>.jpg`: ảnh gốc phóng to từng hình, viền đỏ đã tách.
- Cận cảnh cuống 3D khi người dùng cần soi kỹ: `render(M, rot=0, eye=(0,-140,90))`.
- Font tự dò: DejaVuSans (Linux), Arial (Windows, macOS).

## 6. Giao kết quả và hỏi người dùng

**Gửi gì:**
1. `tong_hop.png` để xem ngay.
2. Từng `khuon_<id>.stl` riêng, kèm file zip cả bộ. Người dùng yêu cầu "xuất từng khuôn 3D riêng".
3. Khi người dùng bảo "xuất hình tôi xem": các `xem_<id>.png` và ảnh đối chiếu 2D.

**Lời nhắn ngắn gồm:**
- lòng khuôn đúng số ghi (hoặc tỷ lệ lấy từ đâu), và thông số khuôn;
- các cách hiểu đã chọn (số ghi sai, khuôn viền trong, "mép thành" = mép lưỡi);
- những chỗ đã sửa khi soát viền;
- hình lệch tỷ lệ, cuống hẹp, khe bị đặc (mục 4);
- một đề nghị bước tiếp theo.

**Khi người dùng chỉ ra chỗ sai** mà chưa rõ chỗ nào: hỏi bằng một trang chọn (kèm ảnh 3D + ảnh đối chiếu, các lựa chọn: khe bị lấp/cạn, răng cưa sai, đế, kích thước, cuống). Sửa **một khuôn trước**, gửi ảnh đối chiếu phóng to vùng đó, duyệt xong mới áp cho các khuôn còn lại.

**Cách gửi/hỏi theo môi trường:**
- **AGS (AgentSEE)** — gọi `ags.exe` bằng đường dẫn đầy đủ:
  - cho xem: `ags view --title "<nói rõ nội dung>" <file...>`;
  - hỏi: `ags form` (trường `media` để kèm ảnh, `radio`/`checkbox` có `suggest`). **Cấm hỏi trong terminal**;
  - gửi Zalo: `ags zalo` (xem `-h`). Dự án hoa đất sét: mọi kết quả gửi vào nhóm **Trạm Test** và tag **chị Nhi Hoa Đất**;
  - việc do agent khác giao (`ags task`): không hỏi lại; gom câu hỏi vào log rồi chốt `task done` kèm danh sách.
- **claude.ai:** SendUserFile — `display: render` cho ảnh, `display: attach` cho STL/zip.
- **Agent khác:** dùng công cụ gửi file/hỏi của hệ thống đó; không có thì in đường dẫn tuyệt đối của từng file.

---

## Phụ lục — config đã duyệt

### Bộ hoa Poppy (có số ghi từng hình, mép 1,0 mm, cách lấy viền cũ)

Ảnh gốc 1841 × 2576 px, khoảng 9 px/mm. 7 khuôn đều kín khối, lòng khuôn đúng số ghi. Dựng lại bằng script mới thì thêm `"contour": "outer"` vào từng hình để ra đúng bản cũ.

```json
{
 "image": "/duong/dan/anh_ban_ve.jpg",
 "out": "/duong/dan/out",
 "set_name": "khuon_hoa_poppy",
 "shapes": [
  {"id": "1_canh_lon", "name": "Cánh lớn", "box": [193, 289, 779, 689], "W": 64, "H": 39, "kind": "petal", "stem_x_frac": 0.47},
  {"id": "2_canh_vua", "name": "Cánh vừa", "box": [850, 386, 1346, 734], "W": 52, "H": 37, "kind": "petal"},
  {"id": "3_canh_nho", "name": "Cánh nhỏ", "box": [1384, 450, 1797, 753], "W": 43, "H": 32, "kind": "petal"},
  {"id": "3b_canh_trong", "name": "Cánh nhỏ (viền trong)", "box": [1384, 450, 1797, 753], "W": 32, "H": 20, "kind": "petal", "contour": "hole", "hole_rank": 1},
  {"id": "4_la_lon", "name": "Lá lớn", "box": [231, 837, 753, 1526], "W": 55, "H": 75, "kind": "leaf"},
  {"id": "5_la_hep", "name": "Lá hẹp", "box": [888, 992, 1101, 1584], "W": 22, "H": 63, "kind": "leaf"},
  {"id": "6_la_xe", "name": "Lá xẻ thuỳ", "box": [1275, 934, 1584, 1526], "W": 34, "H": 63, "kind": "leaf", "thresh": 16}
 ],
 "cutter": {"edge": 1.0}
}
```

### Bộ hoa chân ngỗng A4 (không số ghi, tỷ lệ theo khổ A4, mép 0,5 mm) — 16/10/2026

Ảnh 2439 × 3447 px, scan cắt sát mép giấy A4 → 11,61 px/mm; kích thước làm tròn 0,5 mm. Nét viền có lẫn mực xanh nên tắt lọc chữ xanh. 7 khuôn kín khối sau khi nạp lại STL; cuống hẹp nhất 2,7 mm.

```json
{
 "image": "/duong/dan/20261016_160408.jpg",
 "out": "/duong/dan/out",
 "set_name": "khuon_hoa_chan_ngong_A4",
 "shapes": [
  {"id": "1_canh_nho", "name": "Cánh nhỏ", "box": [162, 482, 490, 957], "W": 21.5, "H": 34.0, "kind": "petal"},
  {"id": "2_canh_vua_nho", "name": "Cánh vừa nhỏ", "box": [601, 465, 1007, 1019], "W": 28.5, "H": 41.5, "kind": "petal"},
  {"id": "3_canh_vua_lon", "name": "Cánh vừa lớn", "box": [1078, 438, 1548, 1063], "W": 34.0, "H": 47.5, "kind": "petal"},
  {"id": "4_canh_lon", "name": "Cánh lớn", "box": [1656, 413, 2210, 1130], "W": 41.0, "H": 55.5, "kind": "petal"},
  {"id": "5_la_vua", "name": "Lá vừa", "box": [158, 1196, 699, 1777], "W": 40.0, "H": 43.0, "kind": "leaf"},
  {"id": "6_la_lon", "name": "Lá lớn", "box": [839, 1265, 1516, 1880], "W": 51.0, "H": 45.0, "kind": "leaf"},
  {"id": "7_la_nho", "name": "Lá nhỏ", "box": [1619, 1368, 2016, 1893], "W": 27.0, "H": 38.0, "kind": "leaf"}
 ],
 "loc_chu_xanh": false
}
```
