import random
import time
import re


def random_name():
    # 팀원 검증용 함수.
    # members_ = re.sub('[][\'\" ]', '', input('입력: ')).split(',') 대신
    # members_ = [random_name() for _ in range(90)] 형태로 사용 할 수 있다.
    first = [
        '서연', '서윤', '지우', '서현',
        '민서', '윤서', '채원', '하윤',
        '지아', '은서', '민준', '서준',
        '주원', '예준', '시우', '준서',
        '도윤', '현우', '건우', '지훈'
    ]
    last = [
        '김', '이', '박', '최',
        '정', '강', '조', '윤',
        '장', '임', '한', '오',
        '서', '신', '권', '황',
        '안', '송', '류', '전',
        '홍', '고', '문', '양',
        '손', '배'
    ]

    name = '{}{}'.format(random.choice(last), random.choice(first))

    return name


def group_maker(set_):
    # loop 만큼의 조가 생성되며, loop-1까지의 조는 7명으로 이루어져 있으며
    # loop조는 set_ % 7만큼의 멤버가 들어간다.
    loop = int(len(set_) / 7) + 1

    data_slice = []
    for _ in range(loop):
        data_slice.append(set_[:7])
        set_[:7] = ''

    return data_slice


def redistribution(slice_data):
    # loop조의 멤버 수가 5미만이라면 loop-1조의 값들에게서 5명이 될 때까지 팀원을 가져온다.
    last_data = slice_data[-1]
    while last_data:
        for d in slice_data[:-1]:
            if len(last_data) >= 5:
                return slice_data
            last_data.append(d.pop())

    return slice_data


def mix_members(mem):
    re_dist = redistribution(group_maker(mem))

    # 조건 3, Dict형식으로 제공하며 key, value는 {1조:[...],}의 형태를 가져야 한다.
    return {'{}조'.format(n): data for n, data in enumerate(re_dist, start=1) if data}


if __name__ == '__main__':
    # 입력 형태 = ['임건우', '배현우', ...]
    # 조건 1, 입력 값은 list형태가 되어야 하므로 str형태의 input 값을 list로 변경
    # members_ = re.sub('[][\'\" ]', '', input('입력: ')).split(',')
    members_ = [random_name() for _ in range(90)]

    start = int(time.time())

    # 조건 2, 팀원의 수는 10명이상 100명 이하이며 그 이외의 값은 잘못된 값이므로 종료한다.
    if not 10 <= len(members_) <= 100:
        print('올바르지 않은 팀원 입력 값입니다. 최소10명에서 최대 100명까지 입력이 가능합니다. 입력된 수 [{}]'.format(len(members_)))
        exit(-1)

    # 조건 4, 동일한 멤버 값이 있는 경우를 대비하여 섞어서 결과 값을 다르게 만든다.
    random.shuffle(members_)

    dic_ = mix_members(members_)

    end = int(time.time())

    print('걸린시간 {}초'.format((end - start) % 60))

    for key, items in dic_.items():
        print(key, items)