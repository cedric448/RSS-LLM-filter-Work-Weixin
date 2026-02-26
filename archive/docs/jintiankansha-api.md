注意
大部分接口需要VIP>=vip1等级以上用户才能使用
查看每个专栏的访问方法
注意：非企业用户的话，所有接口可能会有较大的访问频次限制。
接口列表
API接口一: 通过RSS链接获取内容
API接口二: 获取 专栏 的RSS链接
API接口三: 获取 我的所有订阅专栏的列表
API接口四: 获取 专栏 的原始文章链接列表（返回最近的文章）
API接口一: 通过RSS链接获取内容
URL	请求方法	请求参数	请求参数&结果示例	其它说明
RSS订阅链接	HTTP GET	无	请看下面的示例	需要vip>=vip0
CURL 示例:
curl -v RSS链接
            
API接口二: 获取 专栏 的RSS链接
URL	请求方法	请求参数	请求参数&结果示例	其它说明
http://www.jintiankansha.me/api3/query/column/rss	HTTP GET/POST	
user: 你的邮箱。你的邮件为13167171761@163.com
token: API访问密钥参数, 请勿告诉他人。你的密钥为 IXhXzdNDnO
slug: 专栏的标识，下同。譬如 http://www.jintiankansha.me/column/nGqairAU3Z 中的 nGqairAU3Z
请看下面的示例	
获取rss_link后，请使用Python/Java/Go等RSS客户端解析器解析即可
需要vip>=vip1
CURL 示例:
curl -v 'http://www.jintiankansha.me/api3/query/column/rss?token=IXhXzdNDnO&user=13167171761@163.com&slug='
成功返回的结果示例:
{
    "status": "success",
    "data": {
        "rss_link": "*****"
    },
    "redirect_url": ""
}
失败返回的结果示例:
{
    "status": "error",
    "data": {
        "message": "专栏不存在",
        "field_name": ""
    },
    "redirect_url": ""
}
            
API接口三: 获取 我的所有订阅专栏的列表
URL	请求方法	请求参数	结果	请求参数&结果示例	其它说明
http://www.jintiankansha.me/api3/query/my_columns	HTTP GET/POST	
user: 你的邮箱。你的邮件为13167171761@163.com
token: API访问密钥参数, 请勿告诉他人。你的密钥为 IXhXzdNDnO
page: 页数。默认为1
source:类型
desc: 介绍
name: 名字
slug: 专栏的标识
请看下面的示例	
返回结果中的slug便是该专栏的标识
需要vip>=vip1
CURL 示例:
curl -v 'http://www.jintiankansha.me/api3/query/my_columns?page=1&token=IXhXzdNDnO&user=13167171761@163.com'
成功返回的结果示例:
{
    "status": "success",
    "data": [
        {
            "source": "公众号",
            "image": "",
            "desc": "",
            "name": "思考小龙",
            "slug": "*******"
        }
    ],
    "redirect_url": ""
}
失败返回的结果示例:
{
    "status": "error",
    "data": {
        "message": "***",
        "field_name": ""
    },
    "redirect_url": ""
}
            
API接口四: 获取 专栏 的原始文章链接列表（返回最近的文章）
URL	请求方法	请求参数	请求参数&结果示例	其它说明
http://www.jintiankansha.me/api3/query/get_topics_by_one_column	HTTP GET/POST	
user: 你的邮箱。你的邮件为13167171761@163.com
token: API访问密钥参数, 请勿告诉他人。你的密钥为 IXhXzdNDnO
slug: 专栏的标识。譬如 http://www.jintiankansha.me/column/nGqairAU3Z 中的 nGqairAU3Z
image: 文章封面
author: 专栏名称
name: 文章名称
publish_time: 发布时间，格式可见示例
original_url: 原始链接
is_first: 是否是首篇
只返回最近8篇以内的文章
每天调用次数=每天RSS额度次数
需要vip>=vip1
CURL 示例:
curl -v 'http://www.jintiankansha.me/api3/query/get_topics_by_one_column?token=IXhXzdNDnO&user=13167171761@163.com&slug='
成功返回的结果示例:
{
    "status":"success",
    "data":[
        {
            "image":"http://img.jintiankansha.me/mmbiz_jpg/uGGpF7p7UUzgKp8f0BE8bLxxl68WVFXsHPQAMDQjAtbKOYJoVxPSa2pb5CjNibDmlGl0DLJTmPRDFb7aopSwBow",
            "author":"空军大队长",
            "name":"解读maxr:自动驾驶和太空基建的极致交汇",
            "publish_time":"20210225215710",
            "original_url":"http://mp.weixin.qq.com/s?__biz=MzU3NzY4OTMyMg==&mid=2247484261&idx=1&sn=a41f679eb4c3a22bc1475885f91f6f2a&chksm=fd0180e0ca7609f66f30c9a509cee67ffc606baec9c3a73e72bf69965dbd8f9f3a124c808dcb&scene=0#rd"
        },
        {
            "image":"http://img.jintiankansha.me/mmbiz_jpg/uGGpF7p7UUy37Ub7lDYXlPVcuf4xFt4CL3pknyMpoPGqI2vm3f7RRGbiabibXQiagW7zk3MugHwxUHqts9C4SC1Pw",
            "author":"空军大队长",
            "name":"新春节庆背后的黑科技和相关公司",
            "publish_time":"20210223213958",
            "original_url":"http://mp.weixin.qq.com/s?__biz=MzU3NzY4OTMyMg==&mid=2247484254&idx=1&sn=33734fd867a1eca372ba260a85897e61&chksm=fd0180dbca7609cdeb89abdc88e919033950e22a0fda615874cac0bb98add482f5134d1858ef&scene=0#rd"
        },
        {
            "image":"http://img.jintiankansha.me/mmbiz_jpg/uGGpF7p7UUzMostGuMMKgicfvb5EXDtu3miaTqJ4iaC4g8v5cyscmmWtwp9YwiazVYsY3YkEIak9icEJOgNhkjQowYg",
            "author":"空军大队长",
            "name":"做时间的狱友，读阿里财报",
            "publish_time":"20210205211236",
            "original_url":"http://mp.weixin.qq.com/s?__biz=MzU3NzY4OTMyMg==&mid=2247484247&idx=1&sn=800df59066223677016e41b54b715a61&chksm=fd0180d2ca7609c46360737fb34a6fb701f059e4328f15e632d5ec4bd1561729cd28c80030e7&scene=0#rd"
        },
        {
            "image":"http://img.jintiankansha.me/mmbiz_jpg/uGGpF7p7UUyaY6GbCfruIV5kn4k7FczDddp2pJ4YqbFBicpMdDicV5mbsQIGMtGia9KZYPXHO5g3GR9aicarsv4ytA",
            "author":"空军大队长",
            "name":"下一个妖股集中营：太空",
            "publish_time":"20210202210805",
            "original_url":"http://mp.weixin.qq.com/s?__biz=MzU3NzY4OTMyMg==&mid=2247484239&idx=1&sn=6787412c72e10f392af9e1585c696c51&chksm=fd0180caca7609dc23075e20e3eca8685c37fbbf80081e58e6c448fbb7a8600292d2d5308b0a&scene=0#rd"
        },
        {
            "image":"http://img.jintiankansha.me/mmbiz_jpg/uGGpF7p7UUyBb8TfeSSg1RzPDkicoalJlyfGvz5UOSibb3a0xms74DOheYmZRasRSz83nFBZ1taoLKZfSt48uTwQ",
            "author":"空军大队长",
            "name":"美团是我的卧龙，这只票是我的凤雏",
            "publish_time":"20210131221023",
            "original_url":"http://mp.weixin.qq.com/s?__biz=MzU3NzY4OTMyMg==&mid=2247484232&idx=1&sn=5814c3fac9baa33b288e73a4d480c474&chksm=fd0180cdca7609db5316d6dc2c08936555836aec51c7d3da5adc134804e30bf734386804e376&scene=0#rd"
        }
    ],
    "redirect_url":""
}

失败返回的结果示例:
{
    "status": "error",
    "data": {
        "message": "***",
        "field_name": ""
    },
    "redirect_url": ""
}
