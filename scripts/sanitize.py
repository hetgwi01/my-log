import os
import re

def sanitize(text):
    # 괄호와 공백을 제거하여 URL 친화적으로 변경
    return text.replace('(', '').replace(')', '').replace(' ', '-')

def run_sanitization():
    content_dir = 'content'
    portfolio_path = os.path.join(content_dir, "portfolio")

    if not os.path.exists(content_dir):
        return

    # 1. 파일 내용 안의 위키링크 수정
    for root, dirs, files in os.walk(content_dir):
        # 포트폴리오는 상대경로를 유지하므로 제외
        if root.startswith(portfolio_path):
            continue

        for file in files:
            if file.endswith('.md'):
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # [[파일명|표시이름]] 패턴에서 파일명 부분 정제
                new_content = re.sub(r'\[\[([^|\]]+)(\|[^\]]+)?\]\]',
                                     lambda m: f"[[{sanitize(m.group(1))}{m.group(2) if m.group(2) else ''}]]",
                                     content)

                if content != new_content:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(new_content)

    # 2. 물리적 파일명 변경
    for root, dirs, files in os.walk(content_dir, topdown=False):
        # 포트폴리오는 파일명 변경 시 링크가 깨지므로 제외
        if root.startswith(portfolio_path):
            continue

        for name in files:
            if name.endswith('.md'):
                new_name = sanitize(name)
                if name != new_name:
                    os.rename(os.path.join(root, name), os.path.join(root, new_name))

if __name__ == "__main__":
    run_sanitization()
