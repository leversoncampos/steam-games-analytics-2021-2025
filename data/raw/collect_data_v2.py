import aiohttp
import asyncio
import json
import os
import re
import time
import sys
from tqdm.asyncio import tqdm

# ================= 配置区域 =================

API_KEY = "YOUR_KEY"

# 结果文件名
OUTPUT_FILE = 'steam_data_2021_2025.jsonl'

# 目标年份：2021-2025
TARGET_YEARS = range(2021, 2026)

# AppID 阈值 (2020年后的游戏ID通常很大，这里设为120万以跳过老游戏)
MIN_APP_ID = 1200000 

# 并发数 (Steam 比较严，建议 5)
SEMAPHORE_LIMIT = 5

# 详情页 API
STORE_URL = "http://store.steampowered.com/api/appdetails"

# ================= 代码逻辑 =================

def parse_year(date_str):
    if not date_str: return None
    match = re.search(r'\b(202[1-5])\b', date_str)
    if match:
        return int(match.group(1))
    return None

def load_processed_ids():
    """读取已完成的ID"""
    if not os.path.exists(OUTPUT_FILE):
        return set()
    processed = set()
    print("[系统] 正在读取断点记录...")
    try:
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    if line.strip():
                        data = json.loads(line)
                        processed.add(data['appid'])
                except:
                    continue
    except Exception as e:
        print(f"[警告] 读取断点文件失败: {e}")
    
    print(f"[系统] 已跳过 {len(processed)} 个历史任务。")
    return processed

async def get_app_list_new_api():
    """
    使用 IStoreService 获取全量列表 (带分页 + 详细日志)
    """
    print("\n" + "="*40)
    print("[阶段一] 正在获取 Steam 游戏列表 (IStoreService)...")
    print("="*40)
    
    all_apps = []
    last_appid = 0
    more_items = True
    page_count = 0
    
    # 这里的超时要设置短一点，因为是循环请求
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        while more_items:
            page_count += 1
            # URL: 包含 include_games=true, max_results=10000
            url = f"https://api.steampowered.com/IStoreService/GetAppList/v1/?key={API_KEY}&include_games=true&include_dlc=false&include_software=false&include_videos=false&include_hardware=false&last_appid={last_appid}&max_results=10000"
            
            try:
                # 打印每页的请求日志，让你知道它活着
                print(f"[列表抓取] 第 {page_count} 页 | 正在请求 last_appid={last_appid} ...", end="\r")
                
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # 解析结构
                        if 'response' in data and 'apps' in data['response']:
                            batch = data['response']['apps']
                            
                            if not batch:
                                print(f"\n[列表抓取] 分页结束，最后一页为空。")
                                more_items = False
                                break
                                
                            all_apps.extend(batch)
                            last_appid = batch[-1]['appid'] # 更新游标
                        else:
                            print(f"\n[错误] 返回数据结构异常: {str(data)[:100]}")
                            more_items = False
                    elif response.status == 403:
                         print(f"\n[致命错误] 403 Forbidden - API Key 可能无效或IP被封。")
                         return []
                    else:
                        print(f"\n[错误] 请求失败，状态码: {response.status}")
                        print(f"[调试信息] {await response.text()}")
                        break
                        
                # 稍微休息一下，避免翻页太快
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"\n[网络错误] {e}")
                # 失败重试逻辑可以加，但这里直接中断防止死循环
                break
    
    print(f"\n\n[系统] 列表下载完成！原始总数: {len(all_apps)} 个")
    
    # 过滤 + 排序
    print(f"[系统] 正在过滤 (MIN_APP_ID > {MIN_APP_ID})...")
    target_apps = [app['appid'] for app in all_apps if app['appid'] > MIN_APP_ID]
    target_apps.sort(reverse=True) # 从新到旧爬
    
    print(f"[系统] 过滤后剩余待爬 ID: {len(target_apps)} 个")
    return target_apps

async def worker(session, appid, semaphore, file_handle):
    async with semaphore:
        params = {'appids': appid, 'cc': 'us', 'l': 'english'}
        retry_count = 0
        
        while retry_count < 3:
            try:
                async with session.get(STORE_URL, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if not data or str(appid) not in data or not data[str(appid)]['success']:
                            return # 数据无效
                        
                        game_data = data[str(appid)]['data']
                        
                        # 类型检查
                        if game_data.get('type') != 'game':
                            return

                        date_str = game_data.get('release_date', {}).get('date', '')
                        year = parse_year(date_str)
                        
                        # === 年份筛选 ===
                        if year and year in TARGET_YEARS:
                            def get_str(field):
                                items = game_data.get(field, [])
                                return ";".join([i['description'] for i in items]) if items else ""
                            
                            price_info = game_data.get('price_overview', {})
                            price = price_info.get('final', 0) / 100.0 if price_info else 0.0
                            if game_data.get('is_free'): price = 0.0

                            out_data = {
                                'appid': appid,
                                'name': game_data.get('name'),
                                'release_year': year,
                                'release_date': date_str,
                                'genres': get_str('genres'),
                                'categories': get_str('categories'),
                                'price': price,
                                'recommendations': game_data.get('recommendations', {}).get('total', 0),
                                'developer': ";".join(game_data.get('developers', [])),
                                'publisher': ";".join(game_data.get('publishers', []))
                            }
                            
                            json_str = json.dumps(out_data, ensure_ascii=False)
                            file_handle.write(json_str + "\n")
                            file_handle.flush()
                            return
                        return # 年份不符

                    elif response.status == 429:
                        # 详细打印限流日志
                        # print(f"[限流] ID {appid} 遇到 429，避让 15s...") 
                        await asyncio.sleep(15 + retry_count * 5)
                        retry_count += 1
                    elif response.status >= 500:
                        await asyncio.sleep(2)
                        retry_count += 1
                    else:
                        return
            except Exception as e:
                # print(f"[异常] ID {appid}: {e}")
                await asyncio.sleep(1)
                retry_count += 1
            finally:
                await asyncio.sleep(1.2) # 礼貌延时

async def main():
    print("=== Steam 数据抓取 (2021-2025) 增强版 ===")
    print(f"日志模式: 详细 | 接口: IStoreService (v1)")
    
    # 1. 获取列表 (会打印很多页数日志)
    all_targets = await get_app_list_new_api()
    
    if not all_targets: 
        print("[结束] 未获取到游戏列表，程序退出。")
        return

    # 2. 剔除已完成
    processed = load_processed_ids()
    final_queue = [aid for aid in all_targets if aid not in processed]
    
    count_todo = len(final_queue)
    print(f"\n[阶段二] 开始爬取详情")
    print(f"总数: {len(all_targets)} | 已存: {len(processed)} | 待爬: {count_todo}")
    
    if count_todo == 0:
        print("所有任务已完成！")
        return
    
    semaphore = asyncio.Semaphore(SEMAPHORE_LIMIT)
    
    # 3. 进度条跑起来
    print("[提示] 进度条显示的是【已检查的ID数】，不代表【存入文件的数】(因为要过滤年份)")
    with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
        async with aiohttp.ClientSession() as session:
            tasks = [worker(session, aid, semaphore, f) for aid in final_queue]
            
            # 使用 tqdm 监控
            for _ in tqdm(asyncio.as_completed(tasks), total=len(tasks), unit="chk", ncols=100):
                await _

    print(f"\n[完成] 任务结束！文件保存在: {OUTPUT_FILE}")

if __name__ == '__main__':
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
