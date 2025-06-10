#!/usr/bin/env python3

import subprocess
import os
import sys
import argparse
import json
import requests

class GitCommitAPI:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.endpoint = os.getenv('OPENAI_ENDPOINT')
        if not self.api_key or not self.endpoint:
            raise ValueError("Please export OPENAI_API_KEY and OPENAI_ENDPOINT to your environment before running this script.")
        self.headers = {
            'Content-Type': 'application/json',
            'api-key': self.api_key
        }
        self.valid_cpus = ['imx8mm', 'imx8mp', 'imx93']
        self.valid_machines = ['ROM-5721', 'ROM-5722', 'ROM-2820']
        self.valid_types = ['dts', 'drivers', 'config', 'kconfig', 'script']

    def extract_json_from_markdown(self, content):
        """Extract JSON from Markdown-formatted response"""
        try:
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                json_content = content[json_start:json_end]
                return json.loads(json_content)
            return None
        except Exception as e:
            print(f"Error extracting JSON: {e}")
            return None

    def analyze_with_azure_openai(self, diff_content, category=None):
        """Use Azure OpenAI API to analyze diff content"""
        try:
            category_hint = ""
            if category:
                category_hint = f"\nThe change type for this diff is **{category}**."
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that analyzes git diffs and generates concise structured commit messages."
                },
                {
                    "role": "user",
                    "content": f"""Analyze the following git diff and generate a CONCISE commit message in the format [cpu][machine][type] title followed by details.
The cpu can be: imx8mm, imx8mp, imx93
The machine can be: ROM-5721, ROM-5722, ROM-2820
The type can be: dts, drivers, config, kconfig, script
{category_hint}

Requirements for the response:
1. Title should be brief but descriptive
2. Details should be limited to 2-3 key points maximum
3. Each detail should be short and focused
4. Avoid redundant information
5. Focus only on the most important changes

If any of cpu, machine, or type cannot be determined, set its value to "unknown".

The diff content is:

{diff_content}

Please return a JSON object in this format:
{{
    "cpu": "detected_cpu",
    "machine": "detected_machine",
    "type": "change_type",
    "title": "brief_title",
    "details": ["key_point1", "key_point2"]
}}"""
                }
            ]
            payload = {
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 800
            }
            print("Sending request to Azure OpenAI API...")
            response = requests.post(
                self.endpoint,
                headers=self.headers,
                json=payload
            )
            print(f"Response status code: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                print(f"Generated content: {content}")
                return self.extract_json_from_markdown(content)
            else:
                print(f"API Error: {response.status_code}")
                print(f"Response: {response.text}")
                return None

        except Exception as e:
            print(f"Error analyzing with Azure OpenAI: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_changed_files(self, repo_path):
        """Return a list of changed (unstaged + staged) files"""
        original_dir = os.getcwd()
        os.chdir(repo_path)
        files = set()
        # unstaged
        out = subprocess.check_output(['git', 'diff', '--name-only']).decode().splitlines()
        files.update(out)
        # staged
        out = subprocess.check_output(['git', 'diff', '--cached', '--name-only']).decode().splitlines()
        files.update(out)
        os.chdir(original_dir)
        return list(files)

    def classify_files(self, files):
        """Classify files into dts, config, drivers, script"""
        dts_files, config_files, drivers_files, script_files = [], [], [], []
        for f in files:
            if f.endswith(('.dts', '.dtsi')):
                dts_files.append(f)
            elif any(k in f.lower() for k in ('config', 'kconfig')):
                config_files.append(f)
            elif f.startswith('drivers/') or f.endswith('.c') or f.endswith('.h'):
                drivers_files.append(f)
            elif f.endswith('.sh') or f.endswith('.py') or f.endswith('.pl') or 'build' in f.lower() or 'script' in f.lower():
                script_files.append(f)
        return dts_files, config_files, drivers_files, script_files

    def get_diff_for_files(self, repo_path, files):
        """Get diff for the specified files (staged + unstaged)"""
        if not files:
            return ""
        original_dir = os.getcwd()
        os.chdir(repo_path)
        # staged
        staged = subprocess.check_output(['git', 'diff', '--cached'] + files).decode('utf-8')
        # unstaged
        unstaged = subprocess.check_output(['git', 'diff'] + files).decode('utf-8')
        os.chdir(original_dir)
        return staged + "\n" + unstaged

    def manual_select(self, prompt, valid_list):
        """Let user manually select from valid_list"""
        while True:
            print(f"\n{prompt}")
            for i, v in enumerate(valid_list, 1):
                print(f"{i}. {v}")
            choice = input("Enter number or value: ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(valid_list):
                return valid_list[int(choice) - 1]
            elif choice in valid_list:
                return choice
            else:
                print("Invalid input, please try again.")

    def execute_commit(self, repo_path, files, commit_message):
        """Stage files and commit"""
        if not files:
            return False
        original_dir = os.getcwd()
        os.chdir(repo_path)
        try:
            subprocess.run(['git', 'add'] + files, check=True)
            subprocess.run(['git', 'commit', '-m', commit_message], check=True)
            print(f"Committed: {commit_message.splitlines()[0]}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error during commit: {e}")
            return False
        finally:
            os.chdir(original_dir)

    def push_changes(self, repo_path):
        """Run git push"""
        try:
            subprocess.run(['git', 'push'], cwd=repo_path, check=True)
            print("Successfully pushed changes")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error during push: {e}")
            return False

def process_category(committer, repo_path, files, category):
    if not files:
        return
    diff_content = committer.get_diff_for_files(repo_path, files)
    if not diff_content.strip():
        print(f"No diff for {category.upper()}")
        return
    analysis = committer.analyze_with_azure_openai(diff_content, category=category)
    if not analysis:
        print(f"Failed to analyze {category} changes, skipping.")
        return
    # 手動補全欄位
    cpu = analysis['cpu']
    if not cpu or cpu == "unknown":
        cpu = committer.manual_select("Select CPU type:", committer.valid_cpus)
    machine = analysis['machine']
    if not machine or machine == "unknown":
        machine = committer.manual_select("Select machine type:", committer.valid_machines)
    change_type = analysis['type']
    if not change_type or change_type == "unknown":
        change_type = committer.manual_select("Select change type:", committer.valid_types)
    title = analysis['title']
    details = analysis['details']
    commit_message = f"[{cpu}][{machine}][{change_type}] {title}\n\n" + "\n".join(details)
    print("\nProposed commit message:")
    print("-" * 50)
    print(commit_message)
    print("-" * 50)
    if input(f"\nCommit {category.upper()} changes? (y/n): ").lower() == 'y':
        committer.execute_commit(repo_path, files, commit_message)

def main():
    parser = argparse.ArgumentParser(description='Auto categorize and commit DTS/CONFIG/DRIVERS/SCRIPT using Azure OpenAI')
    parser.add_argument('repo_path', help='Path to the git repository')
    args = parser.parse_args()
    repo_path = args.repo_path

    if not os.path.isdir(repo_path) or not os.path.isdir(os.path.join(repo_path, '.git')):
        print(f"Error: {repo_path} is not a valid git repository")
        return

    committer = GitCommitAPI()
    changed_files = committer.get_changed_files(repo_path)
    if not changed_files:
        print("No changes to commit")
        return

    dts_files, config_files, drivers_files, script_files = committer.classify_files(changed_files)

    if dts_files:
        process_category(committer, repo_path, dts_files, 'dts')
    if config_files:
        process_category(committer, repo_path, config_files, 'config')
    if drivers_files:
        process_category(committer, repo_path, drivers_files, 'drivers')
    if script_files:
        process_category(committer, repo_path, script_files, 'script')

    if input("\nAll commits done. Push now? (y/n): ").lower() == 'y':
        committer.push_changes(repo_path)

if __name__ == "__main__":
    main()