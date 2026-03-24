import { joinSegments, pathToRoot } from "../util/path"
import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"
import { classNames } from "../util/lang"
import { i18n } from "../i18n"

const PageTitle: QuartzComponent = ({ fileData, cfg, displayClass }: QuartzComponentProps) => {
  const title = cfg?.pageTitle ?? i18n(cfg.locale).propertyDefaults.title
  const baseDir = pathToRoot(fileData.slug!)
  
  return (
    <h2 class={classNames(displayClass, "page-title")}>
      <a href={baseDir} class="terminal-nav">
        {/* 1. 로고 이미지 영역 */}
        <div class="logo-wrapper">
          <img 
            src={joinSegments(baseDir, "static/logo.svg")} 
            alt="Terminal Logo" 
            class="terminal-icon"
          />
        </div>
        
        {/* 2. 터미널 텍스트 영역 */}
        <div class="terminal-text">
          <span class="prompt-prefix">~/</span>
          <span class="title-main">{title}</span>
          <span class="blinking-cursor">_</span>
        </div>
      </a>
    </h2>
  )
}

PageTitle.css = `
.page-title {
  margin: 0;
}

.terminal-nav {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  text-decoration: none;
  /* 터미널 느낌을 위해 고정폭 폰트 사용 */
  font-family: 'JetBrains Mono', 'Fira Code', 'IBM Plex Mono', monospace;
}

.logo-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
}

.terminal-icon {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  transition: transform 0.2s ease;
}

.terminal-nav:hover .terminal-icon {
  transform: scale(1.1) rotate(-5deg);
}

.terminal-text {
  display: flex;
  align-items: center;
  font-size: 1.4rem; /* 원본 1.75rem보다 살짝 줄여서 터미널 느낌 강조 */
  letter-spacing: -0.02em;
}

.prompt-prefix {
  color: #7aa2f7; /* 터미널 블루 */
  font-weight: 700;
  margin-right: 0.2rem;
}

.title-main {
  color: var(--dark);
  font-weight: 700;
}

.blinking-cursor {
  color: #73daca; /* 터미널 그린 */
  font-weight: 900;
  margin-left: 2px;
  animation: terminal-blink 1.2s step-end infinite;
}

@keyframes terminal-blink {
  from, to { opacity: 1; }
  50% { opacity: 0; }
}

/* 다크 모드 대응 */
:root[aria-theme='dark'] .title-main {
  color: #c0caf5;
}

.page-title a {
  color: inherit;
}
`

export default (() => PageTitle) satisfies QuartzComponentConstructor