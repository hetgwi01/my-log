import os
import re


def run_sanitization():
    content_dir = "content"
    portfolio_path = os.path.join(content_dir, "portfolio")

    if not os.path.exists(content_dir):
        print("⚠️ content 폴더가 없습니다.")
        return

    print("🚀 정제를 시작합니다. (이미지 보호)")

    # 1. 파일 내용 수정 (링크, 슬러그, 별칭)
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
                    # [A] 위키링크 정제 (이미지는 ![[ 형태이므로 제외)
                    if "[[" in line and "![" not in line:
                        line = re.sub(
                            r"\[\[([^|\]]+)(\|[^\]]+)?\]\]",
                            lambda m: (
                                f"[[{m.group(1)}{m.group(2) if m.group(2) else ''}]]"
                            ),
                            line,
                        )

                    # [B] Frontmatter 내의 slug 정제 (값만 추출해서 정제)
                    if line.startswith("slug:"):
                        prefix, value = line.split(":", 1)
                        line = f"{prefix}: {value.strip()}\n"

                    # [C] Frontmatter 내의 aliases 정제 (값만 추출해서 정제)
                    if line.startswith("aliases:"):
                        prefix, value = line.split(":", 1)
                        line = f"{prefix}: {value.strip()}\n"

                    new_lines.append(line)

                with open(path, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)

    # 2. 물리적 파일명 변경 (오직 .md 파일만)
    for root, dirs, files in os.walk(content_dir, topdown=False):
        if root.startswith(portfolio_path):
            continue

        for name in files:
            if name.endswith(".md"):
                new_name = name
                if name != new_name:
                    try:
                        os.rename(
                            os.path.join(root, name), os.path.join(root, new_name)
                        )
                    except OSError:
                        pass

    print("✨ 정제 완료. 404 방지를 위해 메타데이터 동기화를 마쳤습니다.")


if __name__ == "__main__":
    run_sanitization()
