# 통합 업무 포털 (biz-portal)

경영 대시보드와 HR 챗봇을 단일 IP로 서비스하는 면접용 포트폴리오 사이트입니다.
**모든 데이터는 가상의 데모 데이터입니다.**

🔗 라이브: http://34.83.67.147

## 구성

```
사용자 → Nginx (GCP VM, 80포트)
          ├─ /            랜딩 페이지 (이 저장소)
          ├─ /dashboard/  경영 현황 종합 대시보드 (이 저장소, 정적)
          ├─ /chatbot/    HR 챗봇 → 127.0.0.1:8000 프록시 (별도 저장소: hr-chatbot)
          └─ /api/, /static/  챗봇 API·리소스 프록시
```

- **랜딩 페이지** (`index.html`) — 📊 경영 대시보드 / 💬 HR 챗봇 진입 버튼
- **경영 대시보드** (`dashboard/`) — 노션 "경영 현황 종합 대시보드"를 웹으로 구현
  - `index.html` 종합 현황: KPI·의사결정 안건·핵심 지표 차트·프로젝트 현황
  - `finance.html` 재무: 매출·비용 추이, 고정비/변동비, 현금흐름 예측
  - `people.html` 인력·조직: 부서별 인원·인건비, 입퇴사 현황
  - `recruiting.html` 채용: 칸반 파이프라인, 후보자·포지션 관리
- **기술**: 순수 HTML/CSS/JS + Chart.js(로컬 번들), 외부 CDN 의존 없음, 다크모드 지원
- **데이터**: `dashboard/assets/data.js`에 정적 포함 (2026년 5월 기준 스냅샷)

## 배포 (GCP VM)

```bash
# 1. 정적 파일 업로드
gcloud compute scp --recurse . n8n-instance:/tmp/site --zone=us-west1-b
gcloud compute ssh n8n-instance --zone=us-west1-b \
  --command="sudo rsync -a --delete --exclude=deploy --exclude=.git --exclude=README.md /tmp/site/ /var/www/portfolio/"

# 2. Nginx 설정 (최초 1회)
sudo cp deploy/portfolio.nginx.conf /etc/nginx/sites-available/portfolio
sudo ln -sf /etc/nginx/sites-available/portfolio /etc/nginx/sites-enabled/portfolio
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

모든 응답에 `Cache-Control: no-cache`를 적용해 배포 즉시 반영됩니다.
