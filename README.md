# lam-khuon-cat-3d

Skill làm **khuôn cắt 3D** (cookie / clay cutter) từ bản vẽ hoặc bản scan hình cánh hoa, lá.

Skill tách đường viền và chỉnh đúng số đo ghi tay của từng hình, giữ đúng nét cuống. Kết quả là file STL có mép lưỡi vát, kèm ảnh xem trước 3D và ảnh đối chiếu 2D.

Định dạng theo chuẩn mở [Agent Skills](https://agentskills.io): một thư mục có `SKILL.md`.

## Cấu trúc

```
SKILL.md                  hướng dẫn cho agent (bắt buộc đọc trước)
scripts/khuon3d.py        script đã kiểm chứng: grid → extract → build
scripts/requirements.txt  thư viện Python cần cài
```

## Cài đặt

**Claude Code**

```bash
git clone https://github.com/goccontent/lam-khuon-cat-3d ~/.claude/skills/lam-khuon-cat-3d
```

**claude.ai**

1. Tải `lam-khuon-cat-3d.zip` ở mục Releases.
2. Vào Settings > Features để tải lên.

**Claude API**

1. Tải file zip ở mục Releases.
2. Tải lên qua Skills API (`/v1/skills`).

Lưu ý: môi trường chạy skill trên API không có mạng, nên cần có sẵn `trimesh` và `manifold3d`.

**Agent khác**

1. Tải repo về.
2. Cho agent đọc `SKILL.md`.
3. Cài thư viện:

```bash
pip install -r scripts/requirements.txt
```

## Agent cần có

- chạy được Python 3 và cài được thư viện;
- lệnh `pdfimages` (gói `poppler-utils`) để đọc bản scan PDF;
- font DejaVuSans để in chữ lên ảnh;
- **xem được ảnh**, để soát `kiem_tra_vien.jpg` và `doi_chieu_*_2D.png`;
- gửi file kết quả về cho người dùng.

## Chạy nhanh

```bash
python3 scripts/khuon3d.py grid ANH.jpg out    # lưới toạ độ để chọn khung từng hình
python3 scripts/khuon3d.py extract config.json # tách viền, báo cáo px/mm
python3 scripts/khuon3d.py build config.json   # STL + ảnh xem trước + zip
```

Mẫu `config.json` và thông số khuôn mặc định nằm trong `SKILL.md`.

## Giấy phép

MIT — xem `LICENSE`.
