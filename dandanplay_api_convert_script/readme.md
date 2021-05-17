

简述
===
对[dandanplay](http://www.dandanplay.com/)的部分[远程访问api](https://github.com/kaedei/dandanplay-libraryindex/blob/master/api/API.md)进行反向代理并重构数据，以便在[dandanplay概念版](https://github.com/xyoye/DanDanPlayForAndroid)上的远程访问显示更好看点。

需求
===
* [dandanplay/弹弹play windows版](http://www.dandanplay.com/)：打开远程访问功能（暂不支持web验证和api密钥）

* [dandanplay概念版 安卓端](https://github.com/xyoye/DanDanPlayForAndroid)

* Python3.x：
 
  * [mitmproxy](https://docs.mitmproxy.org/stable/)，按官方的办法用 pip install mitmproxy 安装，不要下载exe因为要调自定义的包
  * PyMysql
  * pypinyin
  * 其他包如果缺少再按照提示安装即可

* Mysql或者其他数据库

* 推荐： nginx或其他有反向代理功能的服务器软件
* 
* 推荐： SQLyog Community等数据库管理软件

使用
===
* 弹弹play：设置远程访问端口号{PORT1} 这里自用的是60119，改成其他端口需要在py脚本里替换。

* 数据库：请在main.py的第31行配置用户名和密码（如果端口改成了非3306也要设置，见pymysql网上的教程和官方文档）

> L31:         self.db = pymysql.connect(host="localhost",user="root",password="000000",database="animedb")

  连接到的数据库为animedb，也可以改成其他的，但需要在下面建立两个表格。

  * uid_path，将媒体库 [/api/v1/library](https://github.com/kaedei/dandanplay-libraryindex/blob/master/api/API.md#8%E8%8E%B7%E5%8F%96%E5%AA%92%E4%BD%93%E5%BA%93%E4%B8%AD%E7%9A%84%E6%89%80%E6%9C%89%E5%86%85%E5%AE%B9-apiv1library) ：
里面的信息进行初步存储（有的也许以后要用）。main.py里面的数据库访问语句（部分）见下面：

  > L59:        sql="""REPLACE INTO uid_path (`Id`, `AnimeId`, `EpisodeId`, `Path`, `Hash`, `AnimeTitle`, `EpisodeTitle`, `FileSize`) VALUES """

![](https://github.com/sunjx17/PyMitmProxyScript_Windows/blob/main/dandanplay_api_convert_script/uid_path.PNG)

  * animetitle_to_group，自定义分组。有的番剧是几个季度的还有剧场版。

![](https://github.com/sunjx17/PyMitmProxyScript_Windows/blob/main/dandanplay_api_convert_script/atitile_group.PNG)

![](https://github.com/sunjx17/PyMitmProxyScript_Windows/blob/main/dandanplay_api_convert_script/atitile_group_example.PNG)

把main.py和imr.py下载至同一目录（并修改好端口号），在命令行定位至该目录下，运行：

>mitmdump -p {PORT2} -m reverse:http://127.0.0.1:{PORT1}/ --set block_global=false -s main.py
>
意思是客户端访问本机:{PORT2}时，由mitmproxy访问弹弹play服务器的{PORT1}并将数据传回客户端，相当于弹弹play的反向代理，并使用main.py对Request和Response的流量进行处理。

这时候就可以用IP:{PORT2}在dandanplay概念版里访问电脑的媒体库了。

推荐用nginx再搭建一层反向代理使用其proxy_cache缓存，或者直接在脚本里面添加一层cache。

说明
===
中间人代理拦截/修改的流量：

* 媒体库 [/api/v1/library](https://github.com/kaedei/dandanplay-libraryindex/blob/master/api/API.md#8%E8%8E%B7%E5%8F%96%E5%AA%92%E4%BD%93%E5%BA%93%E4%B8%AD%E7%9A%84%E6%89%80%E6%9C%89%E5%86%85%E5%AE%B9-apiv1library) ：
弹弹play概念版客户端里的远程访问功能并不完善，默认显示两层，第一层目录和第二层文件名，分别是"Path"字段文件路径的文件目录名和文件名。
例如修改前：
> "PATH": "Y:\\\\anime\\\\佐贺偶像是传奇 S1\\\\\[Zombieland Saga\]\[03\]\[BIG5\]\[1080P\].mp4"
> 
> 第一层显示的目录：佐贺偶像是传奇 S1
> 
> 第二层显示的文件：[Zombieland Saga\]\[03\]\[BIG5\]\[1080P\].mp4

此外还有
> "AnimeTitle": "佐贺偶像是传奇",
> 
> "EpisodeTitle": "第3话 DEAD OR LIVE SAGA",
> 
>……

修改后：
> "PATH": "佐贺偶像是传奇\\\\\S1-第3话 DEAD OR LIVE SAGA"
> 
> 第一层显示的目录改为番剧或系列名：佐贺偶像是传奇
> 
> 第二层显示的文件改为 “季度-分集名称”格式：S1-第3话 DEAD OR LIVE SAGA

这里的“季度”需要在 animetitle_to_group 数据库进行配置，对应其中的GroupName（系列名），EpTitlePrev（季度或子系列前缀）-分集名称。

* 弹幕：对短时间内重复较多的相似弹幕做了处理，合并为一条弹幕并增大字号、在前面加上重复次数，且一般优先使用合并的弹幕中样式较为“高级”的：居中>普通，彩色>白色。

* 字幕：对访问字幕的请求，默认不转发给弹弹play服务端，而是使用存储在uid_path表格里的Path字段信息，在同一目录下寻找给定格式的字幕。
