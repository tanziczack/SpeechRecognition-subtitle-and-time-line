import speech_recognition as sr
import os,pinyin,srt,time,re
from fuzzywuzzy import fuzz
from pydub import AudioSegment
from pydub.silence import split_on_silence, detect_nonsilent

#
def comp_sub(c,h): #对比自动字幕和脚本字幕的匹配度，分数越高越匹配；c代表自动字幕，h代表脚本字幕
    ch_num = {'1': '一', '2': '二', '3': '三', '4': '四', '5': '五', '6': '六', '7': '七', '8': '八', '9': '九', '0': '零'}
    af_h = re.sub(' ', "", re.sub(r'\W', "", re.sub(r'[(（]\w+[)）]', "", h)))
    # 去除脚本字幕中的中英文标点符号、圆括号中的备注内容、空格
    c=re.sub('tzkcaNNotrecognize!',"",c)
    txt = c
    for n in ch_num:
        txt = txt.replace(n, ch_num[n])
    af_c = re.sub(' ', "", txt)  # 把自动字幕中的阿拉伯数字换成汉语数字，去除自动字幕中的空格
    txt = af_h
    for n in ch_num:
        txt = txt.replace(n, ch_num[n])
    af_h = re.sub(' ', "", txt)  # 把脚本字幕中的阿拉伯数字换成汉语数字，去除脚本字幕中的空格
    # 转换成拼音后进行比对
    c_py = pinyin.get(af_c, '', "strip")
    h_py = pinyin.get(af_h, '', "strip")
    res = fuzz.token_set_ratio(c_py, h_py)
    return res

def gen_sub(sub_c,sub_h):  #给字幕打轴,sub_c表示自动字幕列表,sub_h表示脚本字幕列表
    dic_h={}   #用于记录所有脚本字幕的匹配评分
    dic_c={}   #用于记录所有自动字幕的匹配评分
    i = 0     #自动字幕序号（索引）
    res = 0
    res2 = 0
    sub_i=0   #脚本字幕序号（索引）
    ch_num = {'1': '一', '2': '二', '3': '三', '4': '四', '5': '五', '6': '六', '7': '七', '8': '八', '9': '九', '0': '零'}
    sub_file = open(sub_path, "w+")  #为产生打轴的字幕做准备

    while (i < len(sub_c) and sub_i < len(sub_h)):  #只要不到最后一条脚本字幕和最后一条自动字幕就一直循环
        af_sub_h = re.sub(' ', "", re.sub(r'\W', "", re.sub(r'[(（]\w+[)）]', "", sub_h[sub_i])))
        txt = af_sub_h
        for n in ch_num:
            txt = txt.replace(n, ch_num[n])
        af_sub_h = re.sub(' ', "", txt)  # 把脚本字幕中的阿拉伯数字换成汉语数字，去除脚本字幕中的空格
        #去除脚本字幕中的标点符号、圆括号中的内容、空格
        txt=sub_c.__getitem__(i).content
        for n in ch_num:
            txt = txt.replace(n, ch_num[n]) #把自动字幕中的阿拉伯数字转换为汉字数字
        af_sub_c = re.sub(' ', "", txt)  # 去除自动字幕中的空格
        ttt=sub_c.__getitem__(i).content  #为了debug时方便查看当前自动字幕
        zzz=sub_h[sub_i]                  #为了debug是方便查看当前脚本字幕
        # #匹配自动字幕和脚本字幕并获取分数
        res=comp_sub(sub_c.__getitem__(i).content,sub_h[sub_i])

        if(res>score_1):   #如果匹配度大于90则直接将脚本字幕复制给自动字幕
            ttt = sub_c.__getitem__(i).content
            zzz = sub_h[sub_i]
            sub_c.__getitem__(i).content=sub_h[sub_i]
        elif (sub_c.__getitem__(i).content == "tzkcaNNotrecognize!"):  # 如果是没识别出的语音
            #以下是为了便于调试程序
            print("time:", audio_du[i])                          #当前语音时长
            print("c_subtitle:", sub_c.__getitem__(i).content)   #当前自动字幕内容应该是"tzkcaNNotrecognize!"
            print("h_subtitle:",sub_h[sub_i])                  #当前脚本字幕内容
            print("h_length:",len(sub_h[sub_i].strip()))       #当前脚本字幕长度
            print("h_duation:",len(sub_h[sub_i].strip())*word_l)  #读出当前脚本字幕可能需要的时间
            print("h_duation:", audio_du[i] / (len(sub_h[sub_i].strip()) * word_l))
            sub_tmp=re.sub(r'[(（]\w+[)）]',"",sub_h[sub_i].strip())
            time_tmp=audio_du[i]
            if((audio_du[i]/(len(sub_tmp)*word_l))>0.5): #这是模拟汉字字幕时的情况，如果中英文混杂，该模型误差较大
                zzz = sub_h[sub_i]
                tmp = audio_du[i]/(len(sub_tmp)*word_l)  #为了debug是方便查看参数值
                sub_c.__getitem__(i).content=sub_h[sub_i]
            else: #这段可能是杂音，跳过该段语音
                sub_i -= 1  #脚本字幕不动，自动字幕移到下一个（与循环最后的i和sub_i加1一起理解）
        elif((len(re.sub('[a-zA-Z]',"",af_sub_c))>len(re.sub('[a-zA-Z]',"",af_sub_h))) and sub_i+1<len(sub_h)): #如果自动字幕比脚本字幕长，且当前脚本字幕不是最后一条，则将下一个脚本字幕加入对比
            sub_stdc=sub_c.__getitem__(i).content  #对比用的自动字幕
            sub_tmp=sub_h[sub_i]
            dic_h[str(sub_i)] = res  #保存第一次匹配的分数，为了方便匹配分数和相应的脚本字幕能一一对应上，我们把sub_i转换成字符串类型，作为字典的key
            sub_i = int(sub_i)  #后续还需要将sub_i作为脚本字幕序号进行累加，所以再从字符串类型转换成整数型
            sub_i_bgn = sub_i   #记住此次匹配时的第一个脚本字幕序号
            zzz = sub_h[sub_i+1]  #为了debug是方便查看参数值
            kkk=sub_tmp.strip()+sub_h[sub_i+1]
            res2 = comp_sub(sub_stdc,sub_tmp.strip()+sub_h[sub_i+1]) #将当前和下一行的脚本字幕结合在一起后与自动字幕进行匹配
            if (res2>=res): #如果联合下一个脚本字幕一起比对后匹配度更高，则执行以下程序
                while (res2>=res): #如果联合下一个脚本字幕一起比对后匹配度更高，则继续结合下一个脚本字幕比对，直至匹配度降低
                    sub_tmp = sub_tmp.strip() + sub_h[sub_i + 1]
                    sub_i += 1
                    res=res2                         #应该再加一个判断i+1是否大于len(sub_c)
                    # res_h[sub_i] = res
                    dic_h[str(sub_i)]=res
                    sub_i = int(sub_i)
                    if(sub_i+1<len(sub_h)):   #如果sub_i+1不是最后一条脚本字幕
                        zzz=sub_h[sub_i+1]
                        res2=comp_sub(sub_stdc,sub_tmp.strip()+sub_h[sub_i+1])
                    else:
                        break    #如果已经匹配过最后一条脚本字幕则跳出while循环
                if (res>score_2):  #将匹配度最高，且大于80分的脚本字幕赋值给自动字幕
                    ttt = sub_c.__getitem__(i).content
                    zzz = sub_h[sub_i]
                    sub_c.__getitem__(i).content = sub_tmp
                # else:  #如果匹配度最高的得分低于80，则回退直至大于80或者回退到开始比对时的第一个脚本字幕（退无可退了）
                else:    #如果匹配度最高的得分低于80，则回退至一开始比对的脚本字幕
                    sub_i=sub_i_bgn
                    sub_c.__getitem__(i).content = sub_h[sub_i]
            else: #如果联合下一个脚本字幕一起和当前自动字幕比对匹配度反而更低，则直接将当前脚本字幕赋值给自动字幕
                ttt = sub_c.__getitem__(i).content
                zzz = sub_h[sub_i]
                sub_c.__getitem__(i).content = sub_h[sub_i]
        elif((len(re.sub('[a-zA-Z]',"",af_sub_c))<len(re.sub('[a-zA-Z]',"",af_sub_h))) and i+1<len(sub_c)): #如果脚本字幕比自动字幕长，且自动字幕不是最后一条字幕，则将下一个自动字幕加入对比
            sub_stdh=sub_h[sub_i]     #比对用的脚本字幕
            sub_tmp=sub_c.__getitem__(i).content
            i_bgn=i
            # res_c[i] = res
            dic_c[str(i)]=res  #保存第一次匹配的分数，使用字典类型记录匹配的分数，为了便于与自动字幕一一对应，使用str(i)作为字典的key
            i=int(i)
            ttt = sub_c.__getitem__(i+1).content
            zzz = sub_h[sub_i]
            res2=comp_sub(sub_tmp+sub_c.__getitem__(i+1).content,sub_stdh)
            if(res2>=res): #如果结合下一个自动字幕一起比对后匹配度更高，则执行以下程序
                while (res2>=res): #如果联合下一个自动字幕一起比对后匹配度更高，则继续结合下一个脚本字幕比对，直至匹配度降低
                    sub_tmp=sub_tmp+sub_c.__getitem__(i+1).content
                    i += 1
                    res=res2
                    dic_c[str(i)] = res
                    i = int(i)
                    if (i + 1 < len(sub_c)): #如果i+1不是最后一条自动字幕
                        ttt = sub_c.__getitem__(i+1).content
                        zzz = sub_h[sub_i]
                        res2=comp_sub(sub_tmp+sub_c.__getitem__(i+1).content,sub_stdh)
                    else:
                        break  #如果已到最后一条自动字幕则跳出while循环
                if(res>score_2):  #将匹配度最高的自动字幕的结束时间赋值给刚开始的自动字幕结束时间
                    ttt = sub_c.__getitem__(i_bgn).content
                    zzz = sub_h[sub_i]
                    sub_c.__getitem__(i_bgn).content = sub_stdh
                    sub_c.__getitem__(i_bgn).end =sub_c.__getitem__(i).end
                    dn=i
                    while (dn>i_bgn):
                        ttt = sub_c.__getitem__(dn).content
                        sub_c.__delitem__(dn)  #删除匹配过的自动字幕
                        del audio_du[dn]       #删除匹配过的自动字幕对应的时间
                        dn -= 1
                    i = i_bgn  # 回归i计数，结合最后的i加1一起理解
                else: #如果匹配度最高的得分低于80，则回退至一开始比对的自动字幕
                    sub_c.__getitem__(i_bgn).content = sub_stdh
                    i = i_bgn  # 回归i计数，结合最后的i加1一起理解
            else: #如果联合下一个自动字幕一起和当前脚本字幕比对匹配度反而更低，则直接将当前脚本字幕赋值给自动字幕
                ttt = sub_c.__getitem__(i).content
                zzz = sub_h[sub_i]
                sub_c.__getitem__(i).content = sub_h[sub_i]
        else:  #以上情况都不是，直接将脚本字幕覆盖自动字幕
            sub_c.__getitem__(i).content = sub_h[sub_i]
            ttt = sub_c.__getitem__(i).content
            zzz = sub_h[sub_i]
        i += 1      #自动字幕序号加一，读取下一条自动字幕
        sub_i += 1   #脚本字幕序号加一，读取下一条脚本字幕
        af_sub_h=""
        af_sub_c=""
        res=0
        res2=0
        # print(i, sub_i, len(sub_c), len(sub_h))
        # print(i,sub_c.__getitem__(i).content,sub_i,sub_h[sub_i])
    sub_file.writelines(srt.compose(sub_c))  #生成打轴后的字幕
    os.chdir('..')

# a function that splits the audio file into chunks
# and applies speech recognition
def silence_based_conversion(path):
    i = 0   #自动字幕序号
    subs=[] #自动字幕列表变量
    sound = AudioSegment.from_wav(path)  #读取制定目录下的wav格式音频文件
    print("sound.dBFS:",sound.dBFS)
    #silence_thresh是指静音的最大分贝数，因为音频文件的分贝数不固定，所以这里我使用当前语音分贝数乘以一个系数作为静音的阈值
    chunk_time_line=detect_nonsilent(sound,min_silence_len=sl,silence_thresh=sound.dBFS*sthm) #获取每句旁白语音的时长
    chunks = split_on_silence(sound,min_silence_len=sl,silence_thresh=sound.dBFS*sthm) #依据每句旁白之间的静音将整段录音分割为一段一段的旁白录音
    print("chunks num:",len(chunks))
    # 创建存储语音片段的目录
    try:
        os.chdir(work_path)
        os.mkdir('audio_chunks')
    except(FileExistsError):
        pass
    os.chdir('audio_chunks')

    for chunk in chunks:
        chunk_silent = AudioSegment.silent(duration=100)  #在语音片段前后各加上一段100毫秒的静音，防止语音片段太突兀，便于语音识别
        audio_chunk = chunk_silent + chunk + chunk_silent
        print("saving chunk{0}.wav".format(i))
        audio_chunk.export("./chunk{0}.wav".format(i), bitrate='192k', format="wav") # 保存一个一个语音片段
        audio_du.append(chunk_time_line[i][1]-chunk_time_line[i][0])  #保存每个语音片段的时间
        filename = 'chunk' + str(i) + '.wav'
        print("Processing chunk " + str(i))
        r = sr.Recognizer()  #创建识别对象
        with sr.AudioFile(filename) as source:
            # r.adjust_for_ambient_noise(source,duration=0.11)
            # r.adjust_for_ambient_noise(source)#有背景噪音的加上该语句，没有背景噪音的，不加反而识别率更高些
            # audio_listened = r.listen(source) #和record效果好像没区别
            audio_listened = r.record(source)  #读取语音片段
        try:
            rec = r.recognize_google(audio_listened,language='zh')  #识别语音片段
            if i>0:
                chunk_time_line[i][0]=chunk_time_line[i][0]-(sl//2-50)  #将字幕时间往前延展一些，第一个字幕除外
            chunk_time_line[i][1]=chunk_time_line[i][1]+(sl//2-50) #将字幕时间往后延展一些

            start_hhmmss = time.strftime('%H:%M:%S', time.gmtime(chunk_time_line[i][0] // 1000))
            start_ms = str(chunk_time_line[i][0] % 1000)
            start = start_hhmmss + "," + start_ms

            end_hhmmss = time.strftime('%H:%M:%S', time.gmtime(chunk_time_line[i][1] // 1000))
            end_ms = str(chunk_time_line[i][1] % 1000)
            end = end_hhmmss + "," + end_ms
            subs.append(srt.Subtitle(index=i, start=srt.srt_timestamp_to_timedelta(start),
                                     end=srt.srt_timestamp_to_timedelta(end), content=str(srt.make_legal_content(rec))))

        except sr.UnknownValueError:  #如果语音识别不出来，则加入特殊的字符串用以标识该段语音
            print("\033[0;31;40mCould not understand audio\033[0m")
            #尽量将录音文件的噪音清除干净，可参见之前的视频
            start_hhmmss = time.strftime('%H:%M:%S', time.gmtime(chunk_time_line[i][0] // 1000))
            start_ms = str(chunk_time_line[i][0] % 1000)
            start = start_hhmmss + "," + start_ms
            end_hhmmss = time.strftime('%H:%M:%S', time.gmtime(chunk_time_line[i][1] // 1000))
            end_ms = str(chunk_time_line[i][1] % 1000)
            end = end_hhmmss + "," + end_ms
            subs.append(srt.Subtitle(index=i, start=srt.srt_timestamp_to_timedelta(start),
                                     end=srt.srt_timestamp_to_timedelta(end), content="tzkcaNNotrecognize!"))
        except sr.RequestError as e:
            print("Could not request results. check your internet connection")
        i += 1  #自动字幕序号加一
    reco_file = open('C:/work_log/subtitle/recognized.txt', "w+")  #生成自动识别的字幕，供参考
    reco_file.writelines(srt.compose(subs))
    return subs    #返回自动识别的字幕列表

if __name__ == '__main__':
    work_path='C:/work_log/subtitle/'    #工作目录
    hsub_path = 'C:/work_log/subtitle/hand_sub.txt' #脚本字幕
    audio_path = 'C:/work_log/subtitle/test.wav'  # 待识别的wav语音文件
    sub_path='C:/work_log/subtitle/sub.srt'       #打轴后的字幕
    score_1=90  #第一次匹配的分数；分数越高对匹配度要求越高，相应的对语音清晰度以及语音识别率也要求约高
    score_2=0  #结合下一行字幕一起匹配的分数；如果录音清晰度不高，建议先调低score_2，如果实在不行可适当调低score_1
    sl = 500  # 按我的语速静音只少持续500毫秒,太短的话语音片段会被切割的太短，不利于语音识别（可依据个人语速调整）
    word_l=80  #每个汉字的读音的估计时长，单位毫秒
    sthm = 1.5  # 越大静音的阈值越低，越多保留原音；但如果录音比较嘈杂，这个值越大可能造成分割的语音片段越长
    audio_du=[]  #记录每段语音的时长

    with open(hsub_path, 'r', encoding='utf-8') as subt: #打开脚本字幕
        subsh = subt.readlines()
        # print('Enter the audio file path')
        #
        # path = input()
        subsc = silence_based_conversion(audio_path)
        gen_sub(subsc, subsh)  # 产生字幕
        print("字幕已产生！")

