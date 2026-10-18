#!/usr/bin/env python3
"""khuon3d.py — làm khuôn cắt 3D (cookie/clay cutter) từ bản vẽ scan/ảnh chụp.

Lệnh:
  python3 khuon3d.py grid   ANH.jpg OUT_DIR          # ảnh lưới toạ độ pixel để chọn khung crop
  python3 khuon3d.py extract config.json             # tách viền -> raw.json + kiem_tra_vien.jpg + bao cáo px/mm
  python3 khuon3d.py soi     config.json             # OUT/soi/<id>.jpg: phóng to từng hình + viền đỏ để soát kỹ
  python3 khuon3d.py build   config.json             # dựng STL + ảnh 3D + ảnh đối chiếu 2D + zip
  (python3 khuon3d.py all config.json = extract + soi + build)
  Windows: gõ `python` thay cho `python3`.

config.json (toạ độ khung = pixel của ẢNH GỐC, không phải ảnh thu nhỏ):
{
  "image": "/duong/dan/anh.jpg",
  "out": "/duong/dan/out",
  "set_name": "khuon_hoa_poppy",
  "shapes": [
    {"id": "1_canh_lon", "name": "Cánh lớn", "box": [193,289,779,689], "W": 64, "H": 39,
     "kind": "petal", "stem_x_frac": 0.47},
    {"id": "3b_canh_trong", "name": "Cánh nhỏ (viền trong)", "box": [...], "W": 32, "H": 20,
     "kind": "petal", "contour": "hole", "hole_rank": 1},
    {"id": "6_la_xe", "name": "Lá xẻ thuỳ", "box": [...], "W": 34, "H": 63, "kind": "leaf", "thresh": 16}
  ],
  "cutter": {"blade_h": 12, "wall": 1.5, "edge": 0.5, "bevel_h": 3, "base_w": 4, "base_t": 2.5},
  "loc_chu_xanh": true
}
W = chiều ngang, H = chiều dọc của HÌNH (đường viền), đúng như người dùng ghi "W x H".
contour: "trong" (mặc định, giữ khe xẻ thuỳ + mũi răng) | "outer" (cách cũ, mép ngoài + close 13) | "hole" (viền trong hình lồng).
"""
import sys, os, json, glob, zipfile, pickle
import numpy as np

CUT_DEFAULT = dict(blade_h=12.0, wall=1.5, edge=0.5, bevel_h=3.0, base_w=4.0, base_t=2.5)
FONT = next((f for f in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 'C:/Windows/Fonts/arial.ttf',
                          '/System/Library/Fonts/Supplemental/Arial.ttf', '/Library/Fonts/Arial.ttf')
             if os.path.exists(f)), 'DejaVuSans.ttf')


def contour_mode(s):
    return s.get('contour', 'trong')


def imread(path):
    import cv2                                  # đọc được cả đường dẫn có dấu tiếng Việt trên Windows
    return cv2.imdecode(np.fromfile(path, np.uint8), cv2.IMREAD_COLOR)


# ---------------------------------------------------------------- grid
def cmd_grid(img, out):
    import cv2
    os.makedirs(out, exist_ok=True)
    im = imread(img)
    h, w = im.shape[:2]
    s = 1200 / max(h, w)
    v = cv2.resize(im, None, fx=s, fy=s)
    for x in range(0, w, 100):
        c = (0, 0, 255) if x % 500 == 0 else (200, 200, 255)
        cv2.line(v, (int(x * s), 0), (int(x * s), v.shape[0]), c, 1)
        if x % 500 == 0: cv2.putText(v, str(x), (int(x * s) + 2, 15), 0, 0.45, (0, 0, 255), 1)
    for y in range(0, h, 100):
        c = (0, 0, 255) if y % 500 == 0 else (200, 200, 255)
        cv2.line(v, (0, int(y * s)), (v.shape[1], int(y * s)), c, 1)
        if y % 500 == 0: cv2.putText(v, str(y), (2, int(y * s) - 2), 0, 0.45, (0, 0, 255), 1)
    p = os.path.join(out, 'luoi_toa_do.jpg'); cv2.imwrite(p, v)
    print('Ảnh gốc', w, 'x', h, 'px ->', p, '(vạch đậm mỗi 500 px, vạch nhạt mỗi 100 px)')


# ---------------------------------------------------------------- extract
def cmd_extract(cfg):
    import cv2
    out = cfg['out']; os.makedirs(out, exist_ok=True)
    im = imread(cfg['image'])
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.float32)
    b, gg, r = [im[..., i].astype(int) for i in range(3)]
    ink_blue = (b - r > 25)                     # chữ ghi số đo bằng bút bi xanh -> bỏ
    if not cfg.get('loc_chu_xanh', True): ink_blue[:] = False   # nét viền có lẫn mực xanh -> giữ
    small = cv2.resize(g, None, fx=0.1, fy=0.1)
    bg = cv2.resize(cv2.medianBlur(small.astype(np.uint8), 31), (g.shape[1], g.shape[0])).astype(np.float32)
    d = bg - g; d[ink_blue] = 0                 # nền phẳng: nét đậm -> d lớn
    raw, rep = {}, {}
    vis = im.copy()
    for s in cfg['shapes']:
        x0, y0, x1, y1 = s['box']
        c = d[y0:y1, x0:x1]
        m = (c > s.get('thresh', 30)).astype(np.uint8)
        n, lab, st, _ = cv2.connectedComponentsWithStats(m)
        for i in range(1, n):
            if st[i, 4] < 150: m[lab == i] = 0
        k = s.get('close', 1 if contour_mode(s) == 'trong' else 13)   # 'trong' tự nối nét đứt, không cần close
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
        cs, h = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
        if contour_mode(s) == 'trong':
            # lòng trong của nét: nối chỗ đứt <= 2r px, tô loang từ ngoài; khe xẻ thuỳ nằm ngoài nên không bị lấp
            rr = s.get('bridge', 4)
            ke = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * rr + 1, 2 * rr + 1))
            md = cv2.dilate(m, ke)
            ff = np.pad(1 - md, 1, constant_values=1).astype(np.uint8)
            cv2.floodFill(ff, None, (0, 0), 2)
            inn = (ff[1:-1, 1:-1] == 1).astype(np.uint8)
            n2, lab2, st2, _ = cv2.connectedComponentsWithStats(inn)
            inn = (lab2 == 1 + np.argmax(st2[1:, 4])).astype(np.uint8)
            inn = cv2.dilate(inn, ke)
            # cộng lại các cụm nét ôm quanh lòng -> lấy MÉP NGOÀI nét (giữ mũi răng nhọn), khe vẫn hở
            n3, lab3 = cv2.connectedComponents(m)
            near = cv2.dilate(inn, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))) > 0
            keep = np.isin(lab3, np.unique(lab3[near & (m > 0)]))
            reg = ((inn > 0) | keep).astype(np.uint8)
            reg = cv2.morphologyEx(reg, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
            cs, _ = cv2.findContours(reg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            reg = np.zeros_like(reg); cv2.drawContours(reg, cs, -1, 1, -1)
            # cả hai về TÂM NÉT: A = mép ngoài co vào (mũi nhọn đúng, khe chập bị lấp); B = lòng trong nở ra (khe đúng, mũi cụt)
            hk = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            A = cv2.erode(reg, hk); B = cv2.dilate(inn, hk)
            ck = s.get('slit_k', 21)
            Bc = cv2.morphologyEx(B, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ck, ck)))
            reg = ((B > 0) | ((A > 0) & (Bc == 0))).astype(np.uint8)   # chỉ bù phần lồi (mũi), bỏ phần lõm (khe)
            reg = cv2.morphologyEx(reg, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
            cs, h = cv2.findContours(reg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            j = max(range(len(cs)), key=lambda j: cv2.contourArea(cs[j]))
        elif contour_mode(s) == 'hole':
            holes = sorted([j for j in range(len(cs)) if h[0][j][3] != -1], key=lambda j: -cv2.contourArea(cs[j]))
            j = holes[s.get('hole_rank', 1)]
        else:
            j = max(range(len(cs)), key=lambda j: cv2.contourArea(cs[j]))
        cc = cs[j][:, 0, :] + [x0, y0]
        raw[s['id']] = cc.tolist()
        bx, by, bw, bh = cv2.boundingRect(cc)
        rep[s['id']] = dict(w_px=bw, h_px=bh, ppmm_x=round(bw / s['W'], 2), ppmm_y=round(bh / s['H'], 2))
        cv2.polylines(vis, [cc], True, (0, 0, 255), 3)
        cv2.rectangle(vis, (x0, y0), (x1, y1), (255, 160, 0), 2)
        cv2.putText(vis, s['id'], (x0 + 4, y0 + 28), 0, 0.9, (255, 120, 0), 2)
    json.dump(raw, open(os.path.join(out, 'raw.json'), 'w'))
    sc = 1600 / max(vis.shape[:2])
    cv2.imwrite(os.path.join(out, 'kiem_tra_vien.jpg'), cv2.resize(vis, None, fx=sc, fy=sc))
    # báo cáo tỷ lệ: phát hiện số ghi sai (vd 5,5 thay vì 55) và hình lệch tỷ lệ
    allp = [v['ppmm_x'] for v in rep.values()] + [v['ppmm_y'] for v in rep.values()]
    med = float(np.median(allp))
    print('px/mm trung vị = %.2f' % med)
    for k, v in rep.items():
        lech = abs(v['ppmm_x'] / v['ppmm_y'] - 1) * 100
        v['lech_xy_%'] = round(lech, 1)
        flag = []
        if max(v['ppmm_x'], v['ppmm_y']) > med * 1.6 or min(v['ppmm_x'], v['ppmm_y']) < med / 1.6:
            flag.append('NGHI SỐ GHI SAI (so với các hình khác)')
        if lech > 5: flag.append('lệch tỷ lệ %.0f%% -> sẽ bị co/giãn để khớp số ghi' % lech)
        print(f"{k:16s} {v['w_px']}x{v['h_px']} px  px/mm x={v['ppmm_x']} y={v['ppmm_y']}  {'; '.join(flag)}")
    json.dump(rep, open(os.path.join(out, 'bao_cao_ty_le.json'), 'w'), ensure_ascii=False, indent=1)


# ---------------------------------------------------------------- soi
def cmd_soi(cfg):
    """Phóng to từng hình (cạnh dài 1100 px) và vẽ viền đỏ đã tách, để soát kỹ khe, mũi răng, cuống."""
    import cv2
    out = cfg['out']; os.makedirs(os.path.join(out, 'soi'), exist_ok=True)
    raw = json.load(open(os.path.join(out, 'raw.json')))
    im = imread(cfg['image'])
    for s in cfg['shapes']:
        x0, y0, x1, y1 = s['box']; c = im[y0:y1, x0:x1].copy()
        sc = 1100 / max(c.shape[:2]); c = cv2.resize(c, None, fx=sc, fy=sc, interpolation=cv2.INTER_CUBIC)
        cc = (np.array(raw[s['id']]) - [x0, y0]) * sc
        cv2.polylines(c, [cc.astype(np.int32)], True, (0, 0, 255), 2)
        cv2.imwrite(os.path.join(out, 'soi', s['id'] + '.jpg'), c)
    print('Ảnh soát ->', os.path.join(out, 'soi'))


# ---------------------------------------------------------------- shape
def make_shape(s, rawc):
    from shapely.geometry import Polygon, MultiPolygon
    from shapely import affinity
    from scipy.interpolate import splprep, splev
    big = lambda g: max(g.geoms, key=lambda p: p.area) if isinstance(g, MultiPolygon) else g
    W, H, kind = s['W'], s['H'], s['kind']
    half = s.get('stroke_half_px', 2.5)
    p = Polygon(rawc).buffer(0)
    # contour ngoài = mép ngoài nét bút -> co vào tâm nét; contour lỗ = mép trong -> nở ra
    p = p.buffer(0 if contour_mode(s) == 'trong' else half if contour_mode(s) == 'hole' else -half)   # 'trong' đã về tâm nét
    p = big(p.buffer(1.0).buffer(-2.0).buffer(1.0))          # khử nhiễu NHẸ (không dùng 2.5/-5 vì bào mất cuống)
    p = affinity.scale(p, 1, -1, origin=(0, 0))               # ảnh y-xuống -> CAD y-lên
    x0, y0, x1, y1 = p.bounds
    p = affinity.scale(p, W / (x1 - x0), H / (y1 - y0), origin=(x0, y0))
    p = affinity.translate(p, -p.bounds[0], -p.bounds[1])
    c = np.array(p.exterior.coords)
    seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(c, axis=0), axis=1))]
    t = np.arange(0, seg[-1], 0.15)
    x = np.interp(t, seg, c[:, 0]); y = np.interp(t, seg, c[:, 1])
    # vùng cuống: trọng số cao để spline bám sát nét vẽ (giữ góc, gờ, mũi nhọn)
    cx = s['stem_x_frac'] * W if s.get('stem_x_frac') is not None else x[y.argmin()]
    rad, ylim = (7, 8) if kind == 'petal' else (5, 10)
    w = 1 + 12 * np.exp(-((x - cx) / rad) ** 2) * (y < ylim)
    kf = s.get('smooth', 0.02 if kind == 'petal' else 0.003)
    tck, _ = splprep([x, y], w=w, per=1, s=kf * len(x))
    n = 1400 if kind == 'petal' else 2200
    xs, ys = splev(np.linspace(0, 1, n, endpoint=False), tck)
    q = big(Polygon(np.c_[xs, ys]).buffer(0)); b = q.bounds
    q = affinity.scale(q, W / (b[2] - b[0]), H / (b[3] - b[1]), origin=(b[0], b[1]))
    q = affinity.translate(q, -q.bounds[0], -q.bounds[1])
    q = Polygon(q.exterior.coords)
    if not q.exterior.is_ccw: q = Polygon(list(q.exterior.coords)[::-1])
    return q, cx


def make_cutter(sp, cut):
    import trimesh
    import shapely
    wall, edge, H, bh = cut['wall'], cut['edge'], cut['blade_h'], cut['bevel_h']
    sp = shapely.set_precision(sp.simplify(0.005), 0.001)      # bỏ đỉnh sát nhau -> STL float32 không gộp đỉnh hỏng kín khối
    parts = [trimesh.creation.extrude_polygon(sp.buffer(wall + cut['base_w'], quad_segs=32).difference(sp), cut['base_t']),
             trimesh.creation.extrude_polygon(sp.buffer(wall, quad_segs=16).difference(sp), H - bh)]
    N = 12                                                     # 12 lát vát: 0,25 mm/lát, mỏng dần wall -> edge
    for j in range(N):
        z0 = H - bh + bh * j / N; z1 = H - bh + bh * (j + 1) / N + 0.002
        wd = wall - (wall - edge) * (j + 0.5) / N
        m = trimesh.creation.extrude_polygon(sp.buffer(wd, quad_segs=16).difference(sp), z1 - z0)
        m.apply_translation([0, 0, z0]); parts.append(m)
    M = trimesh.boolean.union(parts, engine='manifold')
    M.apply_translation(-M.bounds[0])
    if M.volume < 0: M.invert()
    return M


# ---------------------------------------------------------------- render
def render(M, W=900, Hh=700, ss=3, rot=-8, eye=(0, -250, 235), zoom=1.0):
    import trimesh
    from PIL import Image
    M = M.copy()
    M.apply_translation(-M.bounds.mean(0) * [1, 1, 0])
    M.apply_transform(trimesh.transformations.rotation_matrix(np.radians(rot), [0, 0, 1]))
    sm = trimesh.graph.smooth_shade(M, angle=np.radians(6))
    V, F, VN = sm.vertices, sm.faces, sm.vertex_normals
    fz = sm.face_normals[:, 2]; bevel = (fz > 0.08) & (fz < 0.9)
    eye = np.array(eye, float); tgt = np.array([0, 0, 4.]); f = tgt - eye; f /= np.linalg.norm(f)
    r = np.cross(f, [0, 0, 1]); r /= np.linalg.norm(r); u = np.cross(r, f)
    P = V - eye; x = P @ r; y = P @ u; z = P @ f
    Wp, Hp = W * ss, Hh * ss
    sc = Hp / 2 / np.tan(np.radians(11)) * (180 / (max(M.extents[:2]) + 30)) * zoom
    X = Wp / 2 + sc * x / z; Y = Hp / 2 - sc * y / z
    zb = np.full((Hp, Wp), np.inf); img = np.zeros((Hp, Wp, 3))
    L1 = np.array([-0.4, -0.6, 0.8]); L1 /= np.linalg.norm(L1)
    L2 = np.array([0.6, -0.2, 0.5]); L2 /= np.linalg.norm(L2)
    base = np.array([200, 150, 184.]); bev = np.array([232, 200, 222.])
    for i, (a, b, c) in enumerate(F):
        xs = np.array([X[a], X[b], X[c]]); ys = np.array([Y[a], Y[b], Y[c]])
        x0 = max(int(np.floor(xs.min())), 0); x1 = min(int(np.ceil(xs.max())), Wp - 1)
        y0 = max(int(np.floor(ys.min())), 0); y1 = min(int(np.ceil(ys.max())), Hp - 1)
        if x1 < x0 or y1 < y0: continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        dd = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
        if abs(dd) < 1e-12: continue
        w0 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / dd
        w1 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / dd
        w2 = 1 - w0 - w1
        ins = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not ins.any(): continue
        zz = w0 * z[a] + w1 * z[b] + w2 * z[c]
        sub = zb[y0:y1 + 1, x0:x1 + 1]; upd = ins & (zz < sub)
        if not upd.any(): continue
        sub[upd] = zz[upd]
        n = w0[upd, None] * VN[a] + w1[upd, None] * VN[b] + w2[upd, None] * VN[c]
        n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
        pos = w0[upd, None] * V[a] + w1[upd, None] * V[b] + w2[upd, None] * V[c]
        vd = eye - pos; vd /= np.linalg.norm(vd, axis=1, keepdims=True)
        n[(n * vd).sum(1) < 0] *= -1
        dif = 0.55 * np.clip(n @ L1, 0, 1) + 0.25 * np.clip(n @ L2, 0, 1)
        hh = L1 + vd; hh /= np.linalg.norm(hh, axis=1, keepdims=True)
        spec = 0.18 * np.clip((n * hh).sum(1), 0, 1) ** 40
        col = bev if bevel[i] else base
        img[y0:y1 + 1, x0:x1 + 1][upd] = np.clip(col * (0.30 + dif)[:, None] + 255 * spec[:, None], 0, 255)
    img[np.isinf(zb)] = [236, 237, 240]
    return Image.fromarray(img.astype(np.uint8)).resize((W, Hh), Image.LANCZOS)


def _render_job(args):
    import trimesh
    from PIL import Image, ImageDraw, ImageFont
    stl, png, title, footer, kind = args
    M = trimesh.load(stl)
    im = render(M, rot=-8 if kind == 'petal' else 0, eye=(0, -250, 235) if kind == 'petal' else (0, -230, 260))
    im = im.crop((0, 40, 900, 700))
    can = Image.new('RGB', (900, 780), (236, 237, 240)); can.paste(im, (0, 60))
    d = ImageDraw.Draw(can)
    d.text((450, 40), title, font=ImageFont.truetype(FONT, 30), fill=(70, 60, 70), anchor='mm')
    d.text((450, 750), footer, font=ImageFont.truetype(FONT, 20), fill=(110, 100, 110), anchor='mm')
    can.save(png)
    return png


# ---------------------------------------------------------------- 2D check
def sheet_2d(items, raw, path):
    """items: list of (shape_cfg, coords, cx). Mỗi hàng: toàn hình + phóng to cuống (lưới 1 mm).
    Nét xám dày = bản vẽ gốc (đã chỉnh cùng bbox), nét hồng = đường viền khuôn."""
    from PIL import Image, ImageDraw, ImageFont
    f = ImageFont.truetype(FONT, 20)
    rows = []
    for s, c, cx in items:
        c = np.array(c); W, H = s['W'], s['H']
        r = np.array(raw[s['id']], float); r[:, 1] *= -1
        r = (r - r.min(0)) / (r.max(0) - r.min(0)) * [W, H]
        tiles = []
        for full in (True, False):
            if full: xa, xb, ya, yb, S = -3, W + 3, -3, H + 3, min(420 / (W + 6), 420 / (H + 6))
            else: xa, xb, ya, yb, S = cx - 7, cx + 7, -1.5, 8.5, 30
            w, h = int((xb - xa) * S), int((yb - ya) * S) + 36
            im = Image.new('RGB', (w, h), 'white'); d = ImageDraw.Draw(im)
            for gx in np.arange(np.ceil(xa), xb + 1):
                d.line([((gx - xa) * S, 36), ((gx - xa) * S, h)], fill=(205, 205, 215) if gx % 5 == 0 else (236, 236, 241))
            for gy in np.arange(np.ceil(ya), yb + 1):
                d.line([(0, 36 + (yb - gy) * S), (w, 36 + (yb - gy) * S)], fill=(205, 205, 215) if gy % 5 == 0 else (236, 236, 241))
            tr = lambda p: [((x - xa) * S, 36 + (yb - y) * S) for x, y in p]
            d.line(tr(r) + tr(r[:1]), fill=(165, 165, 165), width=max(3, int(S * 0.3)))
            d.line(tr(c) + tr(c[:1]), fill=(190, 40, 120), width=3)
            d.text((w / 2, 18), f"{s['name']} {W:g}×{H:g}" if full else 'cuống (lưới 1 mm)', font=f, fill='black', anchor='mm')
            tiles.append(im)
        a, b = tiles
        row = Image.new('RGB', (a.width + b.width + 20, max(a.height, b.height)), 'white')
        row.paste(a, (0, 0)); row.paste(b, (a.width + 20, 0)); rows.append(row)
    can = Image.new('RGB', (max(x.width for x in rows), sum(x.height + 10 for x in rows)), 'white'); yy = 0
    for x in rows: can.paste(x, (0, yy)); yy += x.height + 10
    can.save(path)


# ---------------------------------------------------------------- build
def cmd_build(cfg):
    from multiprocessing import Pool
    from PIL import Image
    out = cfg['out']; raw = json.load(open(os.path.join(out, 'raw.json')))
    cut = dict(CUT_DEFAULT, **cfg.get('cutter', {}))
    footer = 'Lưỡi cao %s mm · thân %s mm · mép cắt %s mm · đế %s mm × %s mm' % tuple(
        ('%g' % cut[k]).replace('.', ',') for k in ('blade_h', 'wall', 'edge', 'base_w', 'base_t'))
    shapes, jobs, stls = {}, [], []
    for s in cfg['shapes']:
        q, cx = make_shape(s, raw[s['id']])
        M = make_cutter(q, cut)
        stl = os.path.join(out, f"khuon_{s['id']}.stl"); M.export(stl); stls.append(stl)
        shapes[s['id']] = (list(q.exterior.coords), cx)
        b = q.bounds
        print(f"{s['id']:16s} lòng khuôn {b[2]-b[0]:.2f} x {b[3]-b[1]:.2f} mm | khuôn {M.extents[0]:.1f} x {M.extents[1]:.1f} x {M.extents[2]:.1f} | kín khối={M.is_watertight} | cuống x={cx:.1f}")
        if not M.is_watertight: print('  !!! KHÔNG KÍN KHỐI — kiểm tra lại đường viền')
        import trimesh
        if not trimesh.load(stl).is_watertight: print('  !!! STL NẠP LẠI KHÔNG KÍN KHỐI')
        jobs.append((stl, os.path.join(out, f"xem_{s['id']}.png"), f"{s['name']} — {s['W']:g} × {s['H']:g} mm", footer, s['kind']))
    pickle.dump(shapes, open(os.path.join(out, 'shapes.pkl'), 'wb'))
    with Pool(min(len(jobs), os.cpu_count() or 2)) as pool:
        pngs = pool.map(_render_job, jobs)
    ims = [Image.open(p).resize((450, 390)) for p in pngs]
    rows = (len(ims) + 2) // 3
    can = Image.new('RGB', (1350, 390 * rows), (236, 237, 240))
    for i, im in enumerate(ims): can.paste(im, ((i % 3) * 450, (i // 3) * 390))
    can.save(os.path.join(out, 'tong_hop.png'))
    for kind, name in (('petal', 'doi_chieu_canh_2D.png'), ('leaf', 'doi_chieu_la_2D.png')):
        items = [(s, shapes[s['id']][0], shapes[s['id']][1]) for s in cfg['shapes'] if s['kind'] == kind]
        if items: sheet_2d(items, raw, os.path.join(out, name))
    zp = os.path.join(out, cfg.get('set_name', 'khuon') + '.zip')
    with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED) as z:
        for p in stls + pngs + glob.glob(os.path.join(out, 'doi_chieu_*_2D.png')) + [os.path.join(out, 'tong_hop.png')]:
            z.write(p, os.path.basename(p))
    print('Xong ->', zp)


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'grid': cmd_grid(sys.argv[2], sys.argv[3])
    else:
        cfg = json.load(open(sys.argv[2], encoding='utf-8'))
        if cmd in ('extract', 'all'): cmd_extract(cfg)
        if cmd in ('soi', 'all'): cmd_soi(cfg)
        if cmd in ('build', 'all'): cmd_build(cfg)
