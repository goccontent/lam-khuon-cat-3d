# lam-khuon-cat-3d

Skill làm **khuôn cắt 3D** (cookie / clay cutter) từ bản vẽ hoặc bản scan hình cánh hoa, lá.

Skill tách đường viền (giữ khe xẻ thuỳ, mũi răng, nét cuống) và chỉnh đúng số đo ghi tay của từng hình, hoặc theo tỷ lệ khổ giấy khi bản vẽ không ghi số. Kết quả là file STL kín khối có mép lưỡi vát (mặc định mép 0,5 mm), kèm ảnh xem trước 3D và ảnh đối chiếu 2D.

Định dạng theo chuẩn mở [Agent Skills](https://agentskills.io): một thư mục có `SKILL.md`.

## Cấu trúc

```
SKILL.md                  hướng dẫn cho agent (bắt buộc đọc trước)
LICH_SU.md                lịch sử hình thành: các lần sai/thất bại và bài học cứng (bắt buộc đọc)
scripts/khuon3d.py        script đã kiểm chứng: grid → extract → soi → build
scripts/requirements.txt  thư viện Python cần cài
```

## Cài đặt

**Claude Code**

```bash
git clone https://github.com/goccontent/lam-khuon-cat-3d ~/.claude/skills/lam-khuon-cat-3d
```

**claude.ai và Claude API**

1. Tải file zip: [main.zip](https://github.com/goccontent/lam-khuon-cat-3d/archive/refs/heads/main.zip). Cũng có thể bấm **Code > Download ZIP**.
2. Tải lên claude.ai ở Settings > Features, hoặc tải lên qua Skills API (`/v1/skills`).

Nếu bước tải lên báo lỗi tên thư mục, giải nén ra, đổi tên thư mục `lam-khuon-cat-3d-main` thành `lam-khuon-cat-3d`, rồi nén lại.

Lưu ý với API: môi trường chạy skill trên API không có mạng, nên cần có sẵn `trimesh` và `manifold3d`.

**Agent khác**

1. Tải repo về.
2. Cho agent đọc `SKILL.md`.
3. Cài thư viện:

```bash
pip install -r scripts/requirements.txt
```

## Agent cần có

- chạy được Python 3 và cài được thư viện;
- lệnh `pdfimages` (gói `poppler-utils`) để đọc bản scan PDF, hoặc `pymupdf`;
- font DejaVuSans hoặc Arial để in chữ lên ảnh (script tự dò; chạy được trên Linux, Windows, macOS);
- **xem được ảnh**, để soát `kiem_tra_vien.jpg` và `doi_chieu_*_2D.png`;
- gửi file kết quả về cho người dùng.

## Chạy nhanh

```bash
python3 scripts/khuon3d.py grid ANH.jpg out    # lưới toạ độ để chọn khung từng hình
python3 scripts/khuon3d.py extract config.json # tách viền, báo cáo px/mm
python3 scripts/khuon3d.py soi config.json     # ảnh phóng to từng hình để soát viền
python3 scripts/khuon3d.py build config.json   # STL + ảnh xem trước + zip
```

Windows: gõ `python` thay cho `python3`.

Mẫu `config.json` và thông số khuôn mặc định nằm trong `SKILL.md`.

## Giấy phép

MIT — xem `LICENSE`.
