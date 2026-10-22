# XUMO SPORT MAJMUASI

**XUMO** — sport va dam olish majmuasi uchun ishlab chiqilayotgan, bron qilish, abonementlar, buyurtmalar va to‘lov jarayonlarini boshqarishga mo‘ljallangan full-stack platforma.

> **Holat:** faol ishlab chiqilmoqda. Production uchun xavfsizlik, monitoring, to‘lov provayderlari bilan integratsiya va infratuzilmani alohida tekshirish talab etiladi.

## Imkoniyatlar

- Futbol maydonlari va akademiya xizmatlari
- Tennis kortlari va bron qilish
- Boks mashg‘ulotlari va abonementlar
- Hostel bronlari
- Musobaqalar, chiptalar va buyurtmalar
- Restoran mahsulotlari va buyurtmalari
- Foydalanuvchilar, autentifikatsiya, rollar va admin/dashboard
- Click to‘lovlari, tranzaksiya xavfsizligi hamda moliyaviy hisobotga oid modullar
- Telegram integratsiyasi va fon vazifalari

> Ba’zi funksiyalar ishlab chiqish yoki tekshirish bosqichida bo‘lishi mumkin; ularni tayyor production funksiyasi deb qabul qilmang.

## Texnologiyalar

| Qatlam | Texnologiya |
| --- | --- |
| Backend | Python 3.12, Django 5.2, Django REST Framework |
| Frontend | React 19, Vite 8, React Router |
| Ma’lumotlar bazasi | PostgreSQL 16 |
| Kesh va navbat | Redis 7 |
| Background jobs | Celery, Celery Beat |
| API autentifikatsiyasi | JWT (Simple JWT) |
| Backend server | Gunicorn |
| Konteynerlash | Docker, Docker Compose |
| Testlar | pytest, pytest-django |

## Loyiha tuzilmasi

```text
Xumo/
├── backend/
│   ├── apps/                    # Domen modullari
│   ├── config/
│   │   ├── settings/            # development / production / testing
│   │   └── urls.py
│   ├── tests/                   # Unit, API va integration testlar
│   ├── manage.py
│   └── pytest.ini
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
├── docker/
│   └── backend/
│       └── Dockerfile
├── compose.yaml                # Asosiy xizmatlar
├── compose.test.yaml           # Izolyatsiyalangan test muhiti
├── requirements.txt
└── .env.example
```

## Talablar

- Docker Engine va Docker Compose plugin
- Frontend'ni alohida ishga tushirish uchun Node.js va npm
- Git

## Ishga tushirish

### 1. Repository'ni olish

```bash
git clone https://github.com/isoyevfirdavs8-ops/Xumo.git
cd Xumo
```

### 2. Muhit sozlamalari

```bash
cp .env.example .env
```

**Muhim:** `.env.example` — namuna. Asosiy `compose.yaml` uchun `.env` faylida haqiqiy `SECRET_KEY`, `ALLOWED_HOSTS`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` va backend sozlamalariga mos `DB_*` qiymatlarini belgilash lozim. Lokal va production sirlarini Git'ga qo‘shmang.

`compose.yaml` backend konteynerlari uchun `config.settings.production` ni o‘rnatadi. Shu sababli unda PostgreSQL va production sozlamalari majburiy; `.env.example` dagi SQLite qiymatlari ushbu Compose muhiti uchun tayyor konfiguratsiya emas.

### 3. Backend image'ni yaratish

```bash
docker build \
  -f docker/backend/Dockerfile \
  -t xumo-backend:local \
  .
```

### 4. Docker xizmatlarini ishga tushirish

```bash
docker compose config
docker compose up -d
docker compose ps
```

Asosiy xizmatlar: `web`, `celery`, `celery_beat`, `db`, `redis`.

Backend (lokal host): `http://127.0.0.1:8000`.

> **Ogohlantirish:** mavjud muhitda `docker compose down -v` ishlatmang — volume'lar va PostgreSQL ma’lumotlari o‘chib ketishi mumkin. Production migratsiyalarini oldindan backup va deployment rejasini tayyorlamasdan ishga tushirmang.

### 5. Frontend'ni ishga tushirish

```bash
cd frontend
npm install
npm run dev
```

Vite development manzili: `http://127.0.0.1:5173`. `/api` so‘rovlari lokal backend'ning `127.0.0.1:8000` manziliga proxy qilinadi.

Build tekshiruvi:

```bash
npm run build
```

## Testlar

Test muhiti `compose.test.yaml` orqali **alohida** `db_test` (PostgreSQL, tmpfs) va `redis_test` xizmatlarini ishlatadi. Testlar uchun maxfiy sozlamalarni `.env.testing` ga kiriting; bu faylni commit qilmang.

Misol:

```dotenv
SECRET_KEY=replace-with-a-unique-random-test-key
XUMO_TEST_DB_PASSWORD=replace-with-a-unique-test-password
```

Testlarni ishga tushirish:

```bash
docker compose \
  --env-file .env.testing \
  -f compose.test.yaml \
  run --rm pytest
```

`pytest` konteyneri `config.settings.testing` dan foydalanadi va `./backend` katalogini read-only mount qiladi. Test Compose ham `xumo-backend:local` image'ini ishlatadi — oldin image'ni build qiling.

**Oxirgi lokal tekshiruv:** 539 ta test muvaffaqiyatli o‘tgan (2026-10-22). Bu production'dagi barcha holatlar kafolatlanganini anglatmaydi.

## API

Asosiy yo‘nalishlar `backend/config/urls.py` da qayd etilgan:

| Yo‘nalish | Tavsif |
| --- | --- |
| `/api/v1/auth/` | Autentifikatsiya va foydalanuvchilar |
| `/api/v1/site/` | Sayt ma’lumotlari |
| `/api/v1/football/` | Futbol |
| `/api/v1/tennis/` | Tennis |
| `/api/v1/boxing/` | Boks |
| `/api/v1/hostel/` | Hostel |
| `/api/v1/attendance/` | Davomat |
| `/api/v1/payments/` | To‘lovlar |
| `/api/v1/finance/` | Moliya |
| `/api/v1/dashboard/` | Boshqaruv paneli |
| `/api/v1/telegram/` | Telegram integratsiyasi |

Bu **URL prefikslari**; aniq endpoint va HTTP metodlari tegishli `apps/*/urls.py` fayllarida belgilangan.

## Production xavfsizligi

- `DEBUG=False` va qat’iy `ALLOWED_HOSTS`
- HTTPS, proxy sozlamalari va xavfsiz cookie'lar
- Click/Payme integratsiyalari uchun imzo tekshiruvi, idempotency va moliyaviy reconciliation
- PostgreSQL backup/recovery sinovlari
- Secrets boshqaruvi, minimal DB privilegiyalari va kirishni cheklash
- Monitoring, alerting, audit log va CI/CD

Bu bandlar **production'ga chiqishdan avval tekshiriladigan talablar** bo‘lib, avtomatik ravishda to‘liq joriy etilgan funksiyalar ro‘yxati emas.

## Repository

GitHub: https://github.com/isoyevfirdavs8-ops/Xumo

Loyiha faol rivojlantirilmoqda.
