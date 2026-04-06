import os
import re


def sanitize_for_web(text):
    # 주소창과 매칭 시스템에서 문제를 일으키는 괄호와 공백을 제거합니다.
    return text.replace("(", "").replace(")", "").replace(" ", "-")


def run_sanitization():
    content_dir = "content"
    portfolio_path = os.path.join(content_dir, "portfolio")

    if not os.path.exists(content_dir):
        print("⚠️ content 폴더가 없습니다.")
        return

    print("🚀 정제를 시작합니다. (이미지 보호 및 링크-별칭-파일명 동기화)")

    # 1. 파일 내용 수정 (내부 링크와 메타데이터 정제)
    for root, dirs, files in os.walk(content_dir):
        if root.startswith(portfolio_path):
            continue

        for file in files:
            if file.endswith(".md"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                new_lines = []
                for line in lines:
                    # [A] 위키링크 정제 (이미지는 ![[ 이므로 제외)
                    # [[대상|이름]] 에서 '대상' 부분을 정제하여 파일명과 일치시킵니다.
                    if "[[" in line and "![" not in line:
                        line = re.sub(
                            r"\[\[([^|\]]+)(\|[^\]]+)?\]\]",
                            lambda m: (
                                f"[[{sanitize_for_web(m.group(1))}{m.group(2) if m.group(2) else ''}]]"
                            ),
                            line,
                        )

                    # [B] Frontmatter 내의 slug 정제 (URL 주소 고정)
                    if line.startswith("slug:"):
                        prefix, value = line.split(":", 1)
                        line = f"{prefix}: {sanitize_for_web(value.strip())}\n"

                    # [C] Frontmatter 내의 aliases 정제 (링크가 찾아올 수 있게 별칭도 정제)
                    if line.startswith("aliases:"):
                        prefix, value = line.split(":", 1)
                        line = f"{prefix}: {sanitize_for_web(value.strip())}\n"

                    new_lines.append(line)

                with open(path, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)

    # 2. 물리적 파일명 변경 (정제된 링크가 찾아올 수 있게 파일명도 변경)
    for root, dirs, files in os.walk(content_dir, topdown=False):
        if root.startswith(portfolio_path):
            continue

        for name in files:
            # 오직 .md 파일만 변경하여 이미지 파일 매칭은 유지함
            if name.endswith(".md"):
                new_name = sanitize_for_web(name)
                if name != new_name:
                    try:
                        os.rename(
                            os.path.join(root, name), os.path.join(root, new_name)
                        )
                        print(f"✅ 동기화 완료: {name} -> {new_name}")
                    except OSError:
                        pass

    print(
        "✨ 정제 완료. 이제 괄호 없는 이름으로 '링크-별칭-파일명'이 삼위일체로 매칭됩니다."
    )


if __name__ == "__main__":
    run_sanitization()
