import requests

headers = {
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36",
}


def request_zhihu():
    response = requests.get("https://www.zhihu.com", headers=headers)

    print(response)


def zhihu_2():
    sed = []
    for item in soup.select('li.zm-topic-cat-item'):
        for k in item.select('a'):
            g = "\"%s\"," % (k['href'][1:])
            sed.append(g)
        print(sed)

    return sed


# request_zhihu()

# 变量是有作用域的，任何语言中都是，变量申请的内存在两个地方，一个是栈，一个是堆

# 基础类型（请问都有哪些基础类型？？？？）都是在栈里面，
# 申请的数据都是在堆里面


# 第一：
# 理解下面的情况
if False:
    a = 1  # 基础类型

print(a)  # 会报错哦  代码的作用域就是 冒号，的那个阶梯，变量只能在里买，超过了之后就销毁了


# 第二：
def h():
    a = [1, 2, 3]  # 变量a赋值了一个数组
    return a  # 把a中的数据（数组）取出来 拷贝一份儿 返回，此时a已经没有了


b = h()  # 把拷贝的数据 赋值给b   类似于 b=[1,2,3]
a = h()  # 把拷贝的数据 复制给一个新的a  和上面的a 完全两码事儿，想当于两个村里同名人，压根儿不是一个人

for i in [1, 2, 3]:  # for 是迭代器,  意思就是重复做一件事，只要满足条件
    a = 1  # 申请了一个变量赋值
    print(a)  # 访问变量的内容

# 在for中 a 这个变量申请了多少次?  3次  每一次都是赋值为1，然后在销毁
print(a)  # 报错 冒号是作用域 已经离开了那个冒号的阶梯之外了，访问不到a的变量了

for i in [1, 2, 3]:  # 这里的i是一个变量 和上面的for 里面的i 只是同名而已, 不同的作用域，两码事儿
    print(i)  # 每一次的迭代 i 都是一个新的变量

_dict = {"k": 1, "k1": []}  # 字典是K : v, 其中K是字符串类型， V可以是 基本类型字符、数字，数据类型 包含数组，元组，甚至是、字典
new_dict["k"] = _dict
