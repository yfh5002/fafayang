import os
import requests
import time
import random
import re
from datetime import datetime
import urllib3
from bs4 import BeautifulSoup
import json
import sys
from urllib.parse import urlparse, urljoin, quote

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class GIFSpider:
    def __init__(self, save_path="./表情包合集"):
        """初始化爬虫"""
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        
        if not os.path.isabs(save_path):
            self.save_path = os.path.join(self.script_dir, save_path)
        else:
            self.save_path = save_path
            
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # 手机端User-Agent池，随机切换防反爬
        self.mobile_ua_pool = [
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Android 13; Mobile; rv:109.0) Gecko/109.0 Firefox/109.0'
        ]
        
        self.create_save_directory()
        self.download_count = 0
        self.failed_count = 0
        self.total_found = 0
        self.start_time = None
        self.skip_urls = set()
        
        # 国内可用备用GIF来源
        self.backup_sources = [
            "https://img.soogif.com/",
        ]
    
    def get_random_mobile_header(self):
        """随机手机UA，降低反爬拦截"""
        return {
            'User-Agent': random.choice(self.mobile_ua_pool),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
    def create_save_directory(self):
        """创建保存目录"""
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path)
            print(f"创建文件夹: {self.save_path}")
        else:
            print(f"保存文件夹: {self.save_path}")
    
    def is_valid_gif(self, filepath):
        """检查文件是否是有效的GIF"""
        try:
            with open(filepath, 'rb') as f:
                header = f.read(6)
                if header.startswith(b'GIF87a') or header.startswith(b'GIF89a'):
                    return True
                f.seek(0)
                content = f.read(200)
                if b'<html' in content or b'<!DOCTYPE' in content:
                    return False
            return False
        except:
            return False
    
    def format_time(self, seconds):
        """格式化时间"""
        if seconds < 60:
            return f"{seconds:.0f}秒"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}分{secs}秒"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}小时{minutes}分"
    
    def progress_bar(self, current, total, desc="下载进度"):
        """显示进度条"""
        bar_length = 25
        if total == 0:
            return
        
        progress = current / total
        filled = int(bar_length * progress)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        if self.start_time and current > 0:
            elapsed = time.time() - self.start_time
            avg_time = elapsed / current
            remaining = avg_time * (total - current)
            time_str = f"剩余: {self.format_time(remaining)}"
        else:
            time_str = ""
        
        percent = progress * 100
        sys.stdout.write(f'\r  {desc}: [{bar}] {percent:.1f}% ({current}/{total}) {time_str}')
        sys.stdout.flush()
    
    def is_gif_url(self, url):
        """判断URL是否为GIF图片直链"""
        url_lower = url.lower()
        if url_lower.endswith('.gif'):
            return True
        if '.gif' in url_lower:
            return True
        return False
    
    def download_gif(self, url, filename, retry=3):
        """下载GIF图片"""
        filepath = os.path.join(self.save_path, filename)
        
        if os.path.exists(filepath) and self.is_valid_gif(filepath):
            print(f"  ⏭ 文件已存在: {filename}")
            return True
        
        if url in self.skip_urls:
            return False
        
        if url.startswith('//'):
            url = 'https:' + url
        elif not url.startswith('http'):
            url = 'https://' + url
        
        url = url.split('?')[0]
        url = url.replace('\\', '/')
        
        if not url.startswith('http'):
            print(f"  ❌ 无效URL")
            self.skip_urls.add(url)
            self.failed_count += 1
            return False
        
        if not self.is_gif_url(url):
            print(f"  ❌ 不是GIF图片链接")
            self.skip_urls.add(url)
            self.failed_count += 1
            return False
        
        for attempt in range(retry + 1):
            try:
                if attempt > 0:
                    print(f"\n  🔄 重试 {attempt}/{retry}")
                    time.sleep(random.uniform(1.2, 2.5))
                
                response = requests.get(
                    url, 
                    headers=self.headers, 
                    timeout=25, 
                    stream=True, 
                    verify=False
                )
                
                if response.status_code == 404:
                    print(f"  ❌ 文件不存在 (404)")
                    self.skip_urls.add(url)
                    self.failed_count += 1
                    return False
                elif response.status_code == 403:
                    print(f"  ❌ 访问被拒绝 (403)")
                    self.skip_urls.add(url)
                    self.failed_count += 1
                    return False
                elif response.status_code != 200:
                    print(f"  ⚠ HTTP错误: {response.status_code}")
                    if attempt < retry:
                        continue
                    self.failed_count += 1
                    return False
                
                content_type = response.headers.get('content-type', '').lower()
                if 'gif' not in content_type:
                    print(f"  ⚠ 响应头非GIF: {content_type[:20]}")
                
                total_size = int(response.headers.get('content-length', 0))
                if total_size > 0 and total_size < 1024:
                    print(f"  ⚠ 文件过小 ({total_size}字节，疑似防盗图页面)")
                    self.skip_urls.add(url)
                    self.failed_count += 1
                    return False
                
                with open(filepath, 'wb') as f:
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                percent = (downloaded / total_size) * 100
                                bar_length = 15
                                filled = int(bar_length * percent / 100)
                                bar = '█' * filled + '░' * (bar_length - filled)
                                sys.stdout.write(f'\r    下载: [{bar}] {percent:.0f}%')
                                sys.stdout.flush()
                
                print()
                
                if self.is_valid_gif(filepath):
                    file_size = os.path.getsize(filepath) / 1024
                    self.download_count += 1
                    print(f"  ✅ 成功: {filename} ({file_size:.1f} KB)")
                    return True
                else:
                    os.remove(filepath)
                    print(f"  ❌ 无效GIF文件（防盗跳转页面）")
                    if attempt < retry:
                        continue
                    self.failed_count += 1
                    return False
                    
            except requests.exceptions.Timeout:
                print(f"  ⏰ 下载超时")
                if attempt < retry:
                    continue
                self.failed_count += 1
                return False
            except requests.exceptions.ConnectionError:
                print(f"  🔌 连接失败")
                if attempt < retry:
                    continue
                self.failed_count += 1
                return False
            except Exception as e:
                print(f"  ❌ 错误: {str(e)[:25]}")
                if attempt < retry:
                    continue
                self.failed_count += 1
                return False
        
        return False
    
    def search_soogif(self, keyword, max_pages=2):
        """【替换原失效微闪】SOOGIF国内GIF搜索，可直连"""
        print(f"从 SOOGIF 搜索: {keyword}")
        print("-" * 40)
        all_gif_urls = []
        keyword_enc = quote(keyword)

        for page in range(1, max_pages + 1):
            try:
                page_size = 20
                offset = (page - 1) * page_size
                url = f"https://soogif.com/search?key={keyword_enc}&pn={page}"
                print(f"  第 {page}/{max_pages} 页...")
                headers = self.get_random_mobile_header()

                response = requests.get(url, headers=headers, timeout=15, verify=False)
                response.encoding = 'utf-8'

                if response.status_code != 200:
                    print(f"    请求失败: {response.status_code}")
                    time.sleep(random.uniform(1, 2))
                    continue
                
                html = response.text
                if len(html) < 200:
                    print(f"    页面内容过短，无结果")
                    continue

                gif_urls = []
                soup = BeautifulSoup(html, 'html.parser')

                # 提取预览GIF地址
                items = soup.select('.search-result-item')
                for item in items:
                    img = item.select_one('img.gif-img')
                    if img:
                        src = img.get('data-original') or img.get('src')
                        if src and '.gif' in src.lower():
                            if src.startswith('//'):
                                src = 'https:' + src
                            gif_urls.append(src)
                
                # 正则兜底提取全部gif链接
                pattern = r'https?://[^\s"\'<>]+\.gif'
                found = re.findall(pattern, html)
                gif_urls.extend(found)

                # 清洗去重
                clean_urls = []
                for u in gif_urls:
                    u = u.replace('\\/', '/').replace('\\', '')
                    if u.startswith('//'):
                        u = 'https:' + u
                    if '.gif' in u.lower():
                        u = u.split('?')[0]
                        if u.startswith('http') and u not in clean_urls:
                            clean_urls.append(u)
                
                clean_urls = list(set(clean_urls))
                if clean_urls:
                    all_gif_urls.extend(clean_urls)
                    print(f"    找到 {len(clean_urls)} 个GIF")
                    for i, u in enumerate(clean_urls[:2], 1):
                        print(f"      {i}. {u[:50]}...")
                else:
                    print(f"    本页未找到GIF")
                
                time.sleep(random.uniform(1.5, 2.8))
                
            except Exception as e:
                print(f"    页面异常: {str(e)[:35]}")
                continue
        
        all_gif_urls = list(set(all_gif_urls))
        if all_gif_urls:
            print(f"\nSOOGIF 总共找到 {len(all_gif_urls)} 个GIF")
        else:
            print(f"\nSOOGIF 未匹配到相关GIF")
        return all_gif_urls
    
    def search_backup_gifs(self, keyword):
        """国内备用搜索，移除无法访问的谷歌搜索"""
        print(f"从备用表情包源搜索: {keyword}")
        print("-" * 40)
        all_gif_urls = []
        return list(set(all_gif_urls))
    
    def extract_gifs_from_url(self, url):
        """从指定URL提取GIF链接"""
        print(f"\n从网页提取GIF: {url}")
        print("-" * 40)
        
        try:
            if not (url.startswith('http://') or url.startswith('https://')):
                url = 'https://' + url
            
            # 尝试PC和手机两种headers
            header_list = [self.headers, self.get_random_mobile_header()]
            resp = None
            for headers in header_list:
                try:
                    resp = requests.get(url, headers=headers, timeout=20, verify=False)
                    if resp.status_code == 200:
                        break
                except:
                    continue
            if resp is None:
                print(f"  ❌ 所有请求方式都失败")
                return []
            
            resp.encoding = 'utf-8'
            html = resp.text
            print(f"  ✅ 页面加载成功 (大小: {len(html)} 字节)")
            
            gif_urls = []
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # 查找所有img标签
            img_tags = soup.find_all('img')
            for img in img_tags:
                src = img.get('src') or img.get('data-original') or img.get('data-src')
                if src and '.gif' in src.lower():
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = urljoin(url, src)
                    gif_urls.append(src)
            
            # 查找所有a标签中的GIF链接
            a_tags = soup.find_all('a', href=re.compile(r'\.gif'))
            for a in a_tags:
                href = a.get('href')
                if href and '.gif' in href:
                    if href.startswith('//'):
                        href = 'https:' + href
                    elif href.startswith('/'):
                        href = urljoin(url, href)
                    gif_urls.append(href)
            
            # 使用正则表达式提取
            patterns = [
                r'https?://[^\s"\'<>]+\.gif',
                r'http://[^\s"\'<>]+\.gif',
                r'//[^\s"\'<>]+\.gif',
            ]
            for pattern in patterns:
                found = re.findall(pattern, html)
                for f in found:
                    if f.startswith('//'):
                        f = 'https:' + f
                    if f not in gif_urls:
                        gif_urls.append(f)
            
            # 清理URL
            clean_urls = []
            for u in gif_urls:
                u = u.replace('\\/', '/')
                u = u.replace('\\', '')
                if u.startswith('//'):
                    u = 'https:' + u
                if '.gif' in u.lower():
                    u = u.split('?')[0]
                    clean_urls.append(u)
            
            clean_urls = list(set(clean_urls))
            
            if clean_urls:
                print(f"  ✅ 找到 {len(clean_urls)} 个GIF链接")
                for i, u in enumerate(clean_urls[:5], 1):
                    print(f"    {i}. {u[:60]}...")
            else:
                print(f"  ❌ 未找到GIF链接")
            
            return clean_urls
            
        except Exception as e:
            print(f"  ❌ 错误: {str(e)[:40]}")
            return []
    
    def search_by_keyword(self, keyword, max_pages=2):
        """搜索并下载"""
        print("\n" + "="*60)
        print(f"搜索关键词: {keyword}")
        print("="*60)
        
        self.start_time = time.time()
        self.skip_urls = set()
        
        all_gif_urls = []
        
        # 主搜索源：SOOGIF（替代失效微闪）
        print("\n[主搜索源 - SOOGIF]")
        urls = self.search_soogif(keyword, max_pages)
        if urls:
            all_gif_urls.extend(urls)
            print(f"SOOGIF 找到 {len(urls)} 个GIF")
        
        # 如果主源没找到，尝试备用来源
        if not all_gif_urls:
            print("\n[备用搜索源]")
            urls = self.search_backup_gifs(keyword)
            if urls:
                all_gif_urls.extend(urls)
                print(f"备用源找到 {len(urls)} 个GIF")
        
        all_gif_urls = list(set(all_gif_urls))
        
        if not all_gif_urls:
            print("\n未找到GIF动图")
            print("\n建议:")
            print("  1. 更换通俗关键词，如: 开心表情包、搞笑、可爱")
            print("  2. 使用选项2从网页网址提取GIF")
            print("  3. 直接打开SOOGIF官网搜图复制链接提取")
            return
        
        self.total_found = len(all_gif_urls)
        
        print(f"\n总共找到 {len(all_gif_urls)} 个GIF动图")
        
        max_download = min(len(all_gif_urls), 20)
        if len(all_gif_urls) > 20:
            print(f"  (限制单次最多下载20个)")
            all_gif_urls = all_gif_urls[:20]
        
        print(f"\n开始下载 (共 {len(all_gif_urls)} 个)...")
        print("-" * 40)
        
        self.start_time = time.time()
        
        for idx, gif_url in enumerate(all_gif_urls, 1):
            self.progress_bar(idx-1, len(all_gif_urls), "总体进度")
            
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{keyword}_{timestamp}_{idx:04d}.gif"
                
                print(f"\n\n[{idx}/{len(all_gif_urls)}]")
                self.download_gif(gif_url, filename)
                
                time.sleep(random.uniform(0.8, 2))
                
            except Exception as e:
                print(f"  处理失败: {str(e)[:30]}")
                continue
        
        self.progress_bar(len(all_gif_urls), len(all_gif_urls), "总体进度")
        print("\n")
        
        self.show_summary()
    
    def extract_and_download(self):
        """从网址提取GIF并下载"""
        print("\n" + "="*60)
        print("从网址提取GIF并下载")
        print("="*60)
        print("\n请输入包含GIF的网页URL")
        print("程序会自动提取页面中的所有GIF链接")
        print("-" * 40)
        
        print("📌 推荐可用网站：soogif.com、斗图相关网页")
        print("-" * 40)
        
        url = input("\n请输入网页URL: ").strip()
        if not url:
            print("URL不能为空！")
            return
        
        if not (url.startswith('http://') or url.startswith('https://')):
            url = 'https://' + url
            print(f"  自动添加协议: {url}")
        
        gif_urls = self.extract_gifs_from_url(url)
        
        if not gif_urls:
            print("\n❌ 未找到GIF链接")
            print("\n建议:")
            print("  1. 检查URL是否正确")
            print("  2. 确认页面内包含GIF动图")
            print("  3. 尝试使用选项1关键词搜索")
            return
        
        self.total_found = len(gif_urls)
        
        print(f"\n总共找到 {len(gif_urls)} 个GIF链接")
        
        domain = urlparse(url).netloc.replace('.', '_')
        
        max_download = min(len(gif_urls), 20)
        if len(gif_urls) > 20:
            print(f"  (限制单次最多下载20个)")
            gif_urls = gif_urls[:20]
        
        print(f"\n开始下载 (共 {len(gif_urls)} 个)...")
        print("-" * 40)
        
        self.start_time = time.time()
        self.skip_urls = set()
        
        for idx, gif_url in enumerate(gif_urls, 1):
            self.progress_bar(idx-1, len(gif_urls), "总体进度")
            
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"web_{domain}_{timestamp}_{idx:04d}.gif"
                
                print(f"\n\n[{idx}/{len(gif_urls)}]")
                self.download_gif(gif_url, filename)
                
                time.sleep(random.uniform(0.5, 1.5))
                
            except Exception as e:
                print(f"  处理失败: {str(e)[:30]}")
                continue
        
        self.progress_bar(len(gif_urls), len(gif_urls), "总体进度")
        print("\n")
        
        self.show_summary()
    
    def show_summary(self):
        """显示下载统计总结"""
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        print(f"\n{'='*60}")
        print(f"下载总结")
        print(f"{'='*60}")
        print(f"  成功下载: {self.download_count} 个GIF")
        print(f"  下载失败: {self.failed_count} 个")
        print(f"  保存位置: {self.save_path}")
        print(f"  总共找到: {self.total_found} 个GIF")
        print(f"  总耗时: {self.format_time(elapsed)}")
        
        if os.path.exists(self.save_path):
            files = [f for f in os.listdir(self.save_path) if f.endswith('.gif')]
            valid_files = []
            
            for f in files:
                filepath = os.path.join(self.save_path, f)
                if self.is_valid_gif(filepath):
                    valid_files.append(f)
            
            if valid_files:
                print(f"\n有效GIF文件: {len(valid_files)} 个")
                valid_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.save_path, x)), reverse=True)
                print("最新下载的5个:")
                for f in valid_files[:5]:
                    filepath = os.path.join(self.save_path, f)
                    size = os.path.getsize(filepath) / 1024
                    print(f"    - {f[:40]}{'...' if len(f)>40 else ''} ({size:.1f} KB)")
                if len(valid_files) > 5:
                    print(f"    ... 还有 {len(valid_files)-5} 个文件")
            else:
                print("\n没有有效的GIF文件")
        print(f"{'='*60}\n")
        
        self.download_count = 0
        self.failed_count = 0
        self.total_found = 0
        self.start_time = None
        self.skip_urls = set()

def main():
    """主函数"""
    print("\n" + "="*60)
    print("GIF动图爬虫 v42.0 (修复503报错版)")
    print("="*60)
    print("数据来源: SOOGIF国内表情包图库")
    print("="*60)
    
    spider = GIFSpider(save_path="./表情包合集")
    
    while True:
        print("\n" + "-"*40)
        print("请选择操作:")
        print("  1. 关键词搜索下载 (国内源)")
        print("  2. 输入网址提取GIF")
        print("  3. 打开文件夹")
        print("  4. 查看已下载")
        print("  5. 退出")
        print("-"*40)
        
        choice = input("请输入选项 (1-5): ").strip()
        
        if choice == '1':
            keyword = input("\n请输入搜索关键词: ").strip()
            if not keyword:
                print("关键词不能为空！")
                continue
            
            pages_input = input("请输入搜索页数 (默认2页): ").strip()
            if pages_input.isdigit():
                max_pages = int(pages_input)
                if max_pages < 1:
                    max_pages = 1
                elif max_pages > 5:
                    print("最多限制5页，避免频繁请求封禁")
                    max_pages = 5
            else:
                max_pages = 2
            
            spider.search_by_keyword(keyword, max_pages)
            
        elif choice == '2':
            spider.extract_and_download()
            
        elif choice == '3':
            if os.path.exists(spider.save_path):
                print(f"打开: {spider.save_path}")
                try:
                    os.startfile(spider.save_path)
                except:
                    print(f"请手动打开: {spider.save_path}")
            else:
                print("文件夹不存在")
                
        elif choice == '4':
            print(f"\n已下载的GIF:")
            if os.path.exists(spider.save_path):
                files = [f for f in os.listdir(spider.save_path) if f.endswith('.gif')]
                if files:
                    valid_count = 0
                    files.sort(key=lambda x: os.path.getmtime(os.path.join(spider.save_path, x)), reverse=True)
                    for i, f in enumerate(files, 1):
                        filepath = os.path.join(spider.save_path, f)
                        if spider.is_valid_gif(filepath):
                            valid_count += 1
                            size = os.path.getsize(filepath) / 1024
                            print(f"  {i:3d}. {f[:45]}{'...' if len(f)>45 else ''} ({size:.1f} KB) [有效]")
                        else:
                            print(f"  {i:3d}. {f[:45]}{'...' if len(f)>45 else ''} [无效]")
                    print(f"\n总计: {len(files)} 个 (有效: {valid_count})")
                else:
                    print("  还没有下载任何GIF")
            else:
                print("  文件夹不存在")
                
        elif choice == '5':
            print("再见！")
            break
            
        else:
            print("无效选项，请重新选择")

if __name__ == "__main__":
    try:
        import requests
        from bs4 import BeautifulSoup
        print("依赖库检查通过")
    except ImportError as e:
        print(f"\n缺少必要的库: {e}")
        print("一键安装依赖命令：")
        print("pip install requests beautifulsoup4")
        input("\n按回车键退出...")
        exit()
    
    main()