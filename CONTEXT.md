# itpeflash.haorio.com - 기술사 오답 노트

## Overview
기술사 시험 대비 오답 노트 앱. React 18 (CDN) + Babel. localStorage 기반 CRUD. Obsidian 연동 가능.

**URL:** https://itpeflash.haorio.com
**GitHub:** https://github.com/Haorio-Lab/itpeflash.haorio.com.git
**Obsidian source:** `/mnt/synology/homes/HenryHoy/Drive/ObsidianVault/HenryNote/기술사 오답 노트/`

## Tech Stack
- React 18.3.1 (CDN)
- Babel standalone
- contenteditable + document.execCommand (rich text editor)
- localStorage (NOTES_KEY='oa-notes-v2', STATUS_KEY='oa-statuses')
- History API (browser back support)
- Cloudflare Pages deployment

## File Structure
```
index.html      (720 lines) — complete app
_headers        — CSP, security headers
```

## Data Model

### Note Schema
```javascript
{
  id: string (uuid),
  title: string,
  domain: string (과목, 17 fixed values),
  tags: string[],
  importance: 1|2|3,
  source: string (e.g., "2024년 1회"),
  created: timestamp,
  summary: string,
  problem: string (문제 설명),
  content: string (HTML, rich text),
  mnemonics: string[] (암기두음),
  memo: string (추가 메모),
  deleted: boolean (soft delete → trash → permanent)
}
```

### Storage Keys
```javascript
localStorage['oa-notes-v2'] = JSON.stringify([...notes])
localStorage['oa-statuses'] = JSON.stringify({[noteId]: status})
```

### 17 Fixed Domains
```
소프트웨어 공학, 데이터베이스, 테스트, 인공지능, 경영컨설팅, 빅데이터분석, 보안,
알고리즘, 네트워크, UML, 디자인패턴, 프로젝트 관리, 법제도, 신기술, 주간기술동향,
CAOS, 풀이문제
```

## Key Features

### CRUD Operations
- **Create** — 제목 + 도메인 + 문제 + 내용(HTML) + 암기두음 + 메모 + 중요도/태그/출처
- **Read** — 리스트 + 상세 보기
- **Update** — inline edit, History API로 back button 지원
- **Delete** — soft delete (deleted=true) → 휴지통 → 영구 삭제

### Rich Text Editor
```javascript
function RichEditor({value, onChange, placeholder, minHeight=200}) {
  // contenteditable div with toolbar
  // execCommand: bold, italic, underline, fontSize, foreColor, backColor, insertUnorderedList, etc
  // image resize: click img → floating panel with % presets + custom px
  // getCleanHtml(): strips img-sel class before save
}
```
- Toolbar: B/I/U + 크기 + 색상 + 배경 + 목록 + 이미지 + 수평선
- 이미지 리사이즈: 클릭 → floating panel, getBoundingClientRect() 기반 위치, % 또는 px 입력

### Screens

**1. List View (기본)**
- 카드 그리드, 도메인별 색상, 상태 표시
- 각 카드: 토픽(title+problem 병합) + 내용 요약(HTML 렌더링)
- 상태 메뉴 (3점), 삭제/수정 버튼

**2. Detail View**
- 4개 섹션: 토픽 | 내용 | 암기두음 | 메모
- 수정/삭제 버튼 (본문 기준 우측 정렬)
- 뒤로가기 버튼 (History API 지원)

**3. Card Editor (Create/Edit)**
- 좌측 back 버튼
- 섹션: 토픽/도메인/태그/출처/중요도 + content (RichEditor) + 암기두음 + 메모
- 저장/취소 버튼 (top + content 아래)
- 토픽 내용 필드 제거됨 (title로 통합)

**4. Study Mode**
- 낱장 복습
- 토픽(title+problem), 내용 표시
- 암기 상태 토글, 다음 카드

### CSS Fixes Applied
- `.rc` class for rendered HTML (mirrors `.re-area` editor styles)
- ul/ol/table padding/spacing 모든 뷰에 적용
- img 리사이즈 후 img-sel 클래스 제거 (저장 전 clean)

### Browser History Support
```javascript
const navigate = useCallback((v, s=null) => {
  window.history.pushState({view: v, selId: s?.id || null}, '');
  setView(v);
  setSel(s);
}, []);
```
- back 버튼 클릭 시 popstate 이벤트로 화면 전환
- detail → list, edit → list 등 자동 전환

## Obsidian Integration

### Sample MD File
Path: `/mnt/synology/homes/HenryHoy/Drive/ObsidianVault/HenryNote/기술사 오답 노트/2026-06-18-정규화-3정규형-혼동.md`

```markdown
---
title: 정규화 3정규형 혼동
domain: 데이터베이스
tags:
  - 정규화
  - 데이터 모델링
importance: 2
source: 2024년 1회 기출
created: 2026-06-18
---

## 문제
[문제 내용...]

## 내용
[상세 설명...]

## 암기두음
- [대표 암기두음...]

## 메모
[추가 메모...]
```

### Schema Mapping
```
Obsidian MD ↔ App Note
─────────────────────
title → title
domain → domain
tags[] → tags
importance → importance
source → source
created → created
## 문제 → problem
## 내용 → content (HTML)
## 암기두음 → mnemonics[] (bullet list → array)
## 메모 → memo
```

### WebDAV Mount (Critical)
```
davfs2 mount at: /mnt/synology/...
⚠️  NEVER do recursive scans (find -maxdepth 1 only)
⚠️  WSL OOM-kill risk on full traversal
⚠️  Always touch exact paths only
```

Obsidian vault 읽기 시:
- `ls -la /mnt/synology/homes/HenryHoy/Drive/ObsidianVault/HenryNote/기술사\ 오답\ 노트/`
- `realpath` 확인 필수 (symlink 확인)

## Deployment
```bash
npm run deploy:itpeflash
# → npx wrangler pages deploy sites/itpeflash --project-name=haorio-itpeflash --branch=main --commit-dirty=true
```

## Known Issues & Gotchas

### Rich Content Rendering
- Initially CSS was only on `.re-area` (editor), broke in detail/study views
- **Fixed:** added `.rc` class to all `dangerouslySetInnerHTML` divs + CSS rules

### Image Sizing
- Images defaulted to 100% width
- **Fixed:** click-to-select + floating panel with resize presets

### Obsidian WebDAV
- Partial write crashes leave `.tmp` files
- Clean up before new writes
- Use bounded find commands

## Performance Notes
- Card list can grow large (no pagination yet)
- consider infinite scroll or pagination if >100 cards
- localStorage has ~5-10MB limit (JSON serialization)
- For large datasets: migrate to IndexedDB or Supabase

## Code Architecture
```
App (main state)
├── NoteCard (grid cell)
├── DetailView (selected note)
├── CardEditor (create/edit)
├── StudyMode (single-card learning)
└── RichEditor (contenteditable + toolbar)
```

## Next Steps / Future Work
- [ ] Obsidian auto-sync (watch file, pull MD → parse → localStorage)
- [ ] Pagination / infinite scroll
- [ ] Search / filter by domain / tags
- [ ] Export to PDF
- [ ] Study statistics (accuracy rate, time spent)
- [ ] Spaced repetition algorithm
- [ ] Collaborative editing (multi-user)

## Critical Paths to Maintain
1. **localStorage keys** — change = data loss
2. **Domain list (17 items)** — app depends on fixed set
3. **RichEditor HTML clean** — stripping img-sel class
4. **History API state** — affects browser back behavior

---
**Last updated:** 2026-06-18  
**Created by:** Claude Code (Sonnet 4.6)
