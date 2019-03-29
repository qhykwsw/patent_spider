import xlrd
import pickle
import os
from tqdm import tqdm
import math

# 根据公司名列表初始化一个新的pklfile, 每个公司的第一个专利设置为空列表
def new_companys_pkl(pklfile, companys):
    with open(pklfile, 'wb') as f:
        results = []
        for company in tqdm(companys):
            result = {}
            company = company.strip()
            result['company'] = company
            result['page_size'] = 0
            result['patent'] = {}
            result['patent'][1] = []
            results.append(result)

        pickle.dump(results, f)

# 根据pagesize追加公司专利字典, 并删除pagesize为0的条目
def filter_companys_pkl(pklfile):
    with open(pklfile, 'rb') as f:
        results = pickle.load(f)
    results_filter = []
    for result in results:
        if result['page_size'] == 0:
            continue
        else:
            for page in range(2,result['page_size']+1):
                result['patent'][page] = []
        results_filter.append(result)
    pklfile_filter = pklfile.split('.')[0] + '_filter.pkl'
    with open(pklfile_filter, 'wb') as f:
        pickle.dump(results_filter, f)

# 对step1的pickle文件清空所有专利内容
def delete_companys_pkl(pklfile):
    with open(pklfile, 'rb') as f:
        results = pickle.load(f)
    for result in results:
        result['patent'][1] = []
    pklfile_empty = pklfile.split('.')[0] + '_empty.pkl'
    with open(pklfile_empty, 'wb') as f:
        pickle.dump(results, f)

# 计算单个pklfile文件中包含专利的公司数和页数
def count(pklfile):
    company_num = 0
    page_num = 0
    spider_page_num = 0
    with open(pklfile, 'rb') as f:
        results = pickle.load(f)
    for result in results:
        page_size = result['page_size']
        company = result['company']
        if page_size != 0:
            company_num += 1
        page_num += result['page_size']
        for i in range(1,page_size+1):
        # for i in range(1,2):
            if result['patent'][i] != []:
                spider_page_num += 1
        # else:
        #     print(company)
        # if page_size > 3000:
        #     print(f'{company}共有{page_size}页专利')
    print(f'共有{company_num}/{len(results)}家公司存在专利, 共有{page_num}页专利信息, 已经爬取了{spider_page_num}页')
    return company_num, page_num, spider_page_num

# 计算多个pklfile文件中包含专利的公司数和页数
def count_all(pklfile, num=8):
    company_all = 0
    page_all = 0
    spider_page_all = 0
    for i in range(num):
        pklfile_split = pklfile.split('.')[0] + '_' + str(i) + '.pkl'
        company_num, page_num , spider_page_num = count(pklfile_split)
        company_all += company_num
        page_all += page_num
        spider_page_all += spider_page_num
    print(f'全部{num}个文件共有{company_all}家公司，{page_all}页专利，已经爬取了{spider_page_all}页')

# 输出pklfile文件中的专利内容
def output_content(pklfile):
    with open(pklfile, 'rb') as f:
        results = pickle.load(f)
    for result in results:
    # for result in results[0:1]:
        for num in range(1):
        # for num in range(result['page_size']):
            if result['page_size'] != 0:
                print(result['company'])
                print(result['page_size'])
                print(result['patent'][num+1])

# 对获取了pagesize的pklfile依据需要爬取的专利页数切分为若干等份
def split_content_pkl(pklfile, num=8):
    companys = 0
    page_sizes = []
    with open(pklfile, 'rb') as f:
        results = pickle.load(f)

    for result in results:
        empty_page_size = 0
        for page_num, content in result['patent'].items():
            if content == []:
                empty_page_size += 1
        page_sizes.append(empty_page_size)
        companys += 1
    # print(page_sizes)
    step = math.ceil(sum(page_sizes) / num)
    print(f"还有{companys}家公司，{sum(page_sizes)}页专利需爬取，{num}等份step选取为{step}")
    # print(page_sizes,step)

    # 找到页数大于step的公司，挪到列表开头，以尽量平均分配页数
    for idx, page_size in enumerate(page_sizes):
        if page_size >= step * 0.9:
            print(f"把第{idx}家公司，{results[idx]['company']}，共{page_sizes[idx]}页专利，放在队列首位")
            page_sizes.insert(0, page_sizes.pop(idx))
            results.insert(0, results.pop(idx))

    # steps中存入切分节点
    steps = [0]
    _page_size = 0
    i = 1
    for idx, empty_page_size in enumerate(page_sizes):
        _page_size += empty_page_size
        if _page_size > step * i:
            i += 1
            steps.append(idx+1)

    # 开始依据steps进行切分
    for i in range(num):
        pklfile_split = pklfile.split('.')[0] + '_' + str(i) + '.pkl'
        start = steps[i]
        if i != num-1:
            end = steps[i+1]
        else:
            end = len(results)
        results_split = results[start:end]

        # 输出每段实际总页数
        empty_page_sizes = 0
        for result in results_split:
            for page_num, content in result['patent'].items():
                if content == []:
                    empty_page_sizes += 1
        print(f"第{i}个pickle包含了{len(results_split)}家公司，还有{empty_page_sizes}页专利信息需要爬取")

        # 保存到文件
        with open(pklfile_split, 'wb') as f:
            pickle.dump(results_split, f)

# 可用于将原始的空pklfile切分为若干等份，亦或者按照自己设置的start和end值切分pklfile
def split_pkl(pklfile, num=8, start=0):
    with open(pklfile, 'rb') as f:
        results_all = pickle.load(f)
    results_keep = results_all[:start]
    results = results_all[start:]
    step = math.ceil(len(results) / num)

    if len(results_keep) != 0:
        with open(pklfile.split('.')[0] + '_keep.pkl', 'wb') as f:
            pickle.dump(results_keep, f)

    for i in range(num):
        pklfile_split = pklfile.split('.')[0] + '_' + str(i) + '.pkl'
        # print(pklfile_split)
        start = i * step
        if i != num-1:
            end = (i + 1) * step
        else:
            end = len(results)
        results_split = results[start:end]
        with open(pklfile_split, 'wb') as f:
            pickle.dump(results_split, f)

# 合并几份pklfile为一
def concentrate_pkl(pklfile, num=8):
    results=[]

    # 如果有keep文件，也拼接进来
    pklfile_keep = pklfile.split('.')[0] + '_keep.pkl'
    if os.path.exists(pklfile_keep):
        with open(pklfile_keep, 'rb') as f:
            results_keep = pickle.load(f)
        results.extend(results_keep)

    # 拼接之前分割出去的子文件
    for i in range(num):
        pklfile_split = pklfile.split('.')[0] + '_' + str(i) + '.pkl'
        with open(pklfile_split, 'rb') as f:
            results_split = pickle.load(f)
        results.extend(results_split)

    # print(len(results))
    with open(pklfile, 'wb') as f:
        pickle.dump(results, f)

# 对一家包含了很多专利的公司进行切分，注意该pickle文件只能包含这单独一家
def split_one_company_pkl(pklfile, num=4, start=1):
    with open(pklfile, 'rb') as f:
        result = pickle.load(f)[0]
        company = result['company']
        page_size = result['page_size']
        patents_all = result['patent']
    patents_keep = {k: v for k, v in patents_all.items() if k < start}
    result_keep = [{'company':company,'page_size':page_size,'patent':patents_keep}]

    if start != 1:
        with open(pklfile.split('.')[0] + '_keep.pkl', 'wb') as f:
            pickle.dump(result_keep, f)

    step = math.floor((len(patents_all)-start+1) / num)

    for i in range(num):
        pklfile_split = pklfile.split('.')[0] + '_' + str(i) + '.pkl'
        begin = i * step + start
        if i != num-1:
            end = (i + 1) * step + start
        else:
            end = len(patents_all) + 1
        patents_split = {k: v for k, v in patents_all.items() if k >= begin and k < end}
        result_split = [{'company':company,'page_size':page_size,'patent':patents_split}]

        with open(pklfile_split, 'wb') as f:
            pickle.dump(result_split, f)

# 对上一步切分出去的同一家公司的专利进行整合
def concentrate_one_company_pkl(pklfile, num=4):
    patents = {}

    pklfile_keep = pklfile.split('.')[0] + '_keep.pkl'
    if os.path.exists(pklfile_keep):
        with open(pklfile_keep, 'rb') as f:
            result_keep = pickle.load(f)[0]
            company = result_keep['company']
            page_size = result_keep['page_size']
            patents_keep = result_keep['patent']

        patents.update(patents_keep)

    for i in range(num):
        pklfile_split = pklfile.split('.')[0] + '_' + str(i) + '.pkl'
        with open(pklfile_split, 'rb') as f:
            patents_split = pickle.load(f)[0]['patent']
        patents.update(patents_split)

    results = [{'company':company,'page_size':page_size,'patent':patents}]

    with open(pklfile, 'wb') as f:
        pickle.dump(results, f)
        
def main():
    excelfile='C:\\Files\\Documents\\apollo项目组\\国防科工局成果转化目录\\海淀区的企业名称.xlsx'
    # patent_class = 'publish'
    # patent_class = 'authorization'
    # patent_class = 'utility_model'
    patent_class = 'design'

    pklfile_step1 = 'results\\' + patent_class + '\\' + patent_class + '_step1.pkl'
    pklfile_step2 = 'results\\' + patent_class + '\\' + patent_class + '_step2.pkl'

    pklfile = 'results\\' + patent_class + '\\' + patent_class + '.pkl'
    pklfile_0 = 'results\\' + patent_class + '\\' + patent_class + '_0.pkl'
    pklfile_1 = 'results\\' + patent_class + '\\' + patent_class + '_1.pkl'
    pklfile_7 = 'results\\' + patent_class + '\\' + patent_class + '_7.pkl'

    pklfile_filter = 'results\\' + patent_class + '\\' + patent_class + '_filter.pkl'

    # # create a new pkl file
    # wb = xlrd.open_workbook(excelfile)
    # sheet = wb.sheet_by_name('Sheet1')
    # companys = sheet.col_values(0)[1:8672]
    # new_companys_pkl(pklfile, companys)
    # split_pkl(pklfile, num=8)
    # split_pkl(pklfile_7, start=925, num=6)

    # delete_companys_pkl(pklfile_step1)

    # count(pklfile_step1)
    # filter_companys_pkl(pklfile)

    # count(pklfile_step2)

    # count_all(pklfile_7, num=6)
    # concentrate_pkl(pklfile_7, num=6)

    # count_all(pklfile, num=8)

    # concentrate_pkl(pklfile, num=8)
    # filter_companys_pkl(pklfile)
    # split_content_pkl(pklfile, num=8)

    output_content(pklfile_step1)
    
if __name__ == "__main__":
    main()
