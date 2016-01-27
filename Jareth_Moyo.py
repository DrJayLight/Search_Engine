__author__ = 'jarethmoyo'



from Tkinter import*
import ttk
import timeit
import re
import os
import searchengine
from operator import itemgetter

path='metadata'


#This class will be responsible for fetching the data from the database metadata and so forth
class DataFetcher:
    def __init__(self, path):
        self.path=path

    def paperdata_loader(self):
        self.titles={}
        wordlocations={}
        dirs=os.listdir(self.path)
        print len(dirs)
        for i in range(len(dirs)):
            pathname=os.path.join(self.path, dirs[i])
            fin=open(pathname)
            string=''
            for line in fin:
                string+=line
            m=re.search(r'\\+(.*?)\\+(.*?[\\].*)[\\]',string,re.MULTILINE|re.DOTALL)
            head= m.group(1)
            body= m.group(2)
            n=re.search(r'Paper:.*?(\d+).*?',head,re.MULTILINE|re.DOTALL)
            n2=re.search(r'Title:\s*(.*)[\n]?',string,re.MULTILINE)
            paperid=n.group(1)
            title=n2.group(1)
            self.titles[str(paperid)]=title
            totabs=title+body
            divider = re.compile('\\W*')
            wordlist=[s.lower() for s in divider.split(totabs) if s != '' and len(s)>1 and s.isalpha()]

            for index, word in enumerate(wordlist):
                if word not in wordlocations:
                    wordlocations.setdefault(word,{})
                    wordlocations[word][paperid]=[index]
                else:
                    if paperid in wordlocations[word]:
                        wordlocations[word][paperid].append(index)
                    else:
                        wordlocations[word][paperid]=[index]
        self.wordlocations=wordlocations

    def citation_data_loader(self):
        citations={}
        citationcounts={}
        gin=open('citations.txt')
        string2=''
        for line in gin:
            string2+=line
        #print string2[0:200]
        divider = re.compile('\\W*')
        lst=[x.lower() for x in divider.split(string2) if x!= '']
        del lst[0:6]
        lst2=[]
        for i in range(1,len(lst),2):
            lst2.append((lst[i-1],lst[i]))
        #print lst2[0:20]
        for id1,id2 in lst2:
            citations.setdefault(id2,[])
            citations[id2].append(id1)
            if id1 not in citationcounts:
                citationcounts.setdefault(id1,1)
            else:
                citationcounts[id1]+=1

        self.citations=citations
        self.citationcounts=citationcounts

    def pagerank_calculator(self, iterations=20):
        pageranks={}
        for item in self.citations:
            pageranks.setdefault(item,1.0)
        for i in range(iterations):
            #print 'Iteration' %i
            pr=0.15
            for item in pageranks:
                init_score=0
                for element in self.citations[item]:
                    if element not in pageranks:
                        val=1.0
                    else:
                        val=pageranks[element]
                    linknum=self.citationcounts[element]
                    init_score+=float(val/linknum)
                pageranks[item]=pr+(0.85*init_score)
        inst=searchengine.searcher('database')
        pageranks=inst.normalizescores(pageranks)
        #print pageranks['9402117']
        self.pagerankscore=pageranks

    def content_based_calculator(self, stringofwords):
        divider = re.compile('\\W*')
        res=[x.lower() for x in divider.split(stringofwords) if x!= '']
        content_scores={}
        paperid_index={}
        content_out={}
        index=1
        for word in res:
            if word in self.wordlocations:
                for papid in self.wordlocations[word]:
                    papid_score=len(self.wordlocations[word][papid])
                    if papid not in content_scores:
                        content_scores[papid]=papid_score
                        paperid_index[papid]=index
                    else:
                        content_scores[papid]=content_scores[papid]*papid_score
                        paperid_index[papid]+=1
            else:
                continue

        for pid in paperid_index:
            if paperid_index[pid]==len(res):
                content_out[pid]=content_scores[pid]

        inst=searchengine.searcher('database')
        content_out=inst.normalizescores(content_out)
        self.contentscore= content_out

    def almagamate(self):
        overallscore={}
        for item in self.contentscore:
            try:
                overallscore[item]=self.contentscore[item]+self.pagerankscore[item]
            except:
                continue
        sorted_score=sorted(overallscore.items(),key=itemgetter(1),reverse=True)
        self.sorted_score= sorted_score

    def final_output(self):
        final_out=[]
        for pid,score in self.sorted_score:
            if pid in self.titles:
                final_out.append((self.titles[pid],score))
        return final_out


class App:
    def __init__(self,master):
        master.title('A JCK PRODUCTION')
        frame1=Frame(master)
        frame1.pack()
        frame2=Frame(master)
        frame2.pack()
        frame3=Frame(frame2)
        frame3.pack(anchor=E,side=BOTTOM,pady=5)
        L1=Label(frame1, text='Digital Library Search Engine',width=45,height=2,bg='orange',
                 font='Verdana 20 bold',fg='white')
        L1.pack()
        self.T1= Text(frame1, width=50,height=1, font='Times 20')
        self.T1.pack(pady=15)
        self.B1=Button(frame1, width=20,height=1,text='Initialize',font='Helvetica 15',fg='darkblue',
                       command=self.init_search)
        self.B1.pack(pady=2)
        self.L3=Label(frame2, text='0 papers',font='Helvetica 12',fg='grey')
        self.L3.pack(anchor=W)
        self.T2=Text(frame2,width=85,height=21, font='Times 12')
        self.T2.pack(pady=10)
        self.B2=Button(frame3,width=10,text='Previous',font='Helvetica 12',fg='blue',command=self.prev_command)
        self.B2.pack(side=LEFT)
        self.L2=Label(frame3, width=5,text='1',font='Times 10',fg='darkgreen')
        self.L2.pack(side=LEFT)
        self.B2=Button(frame3,width=10,text='Next',font='Helvetica 12',fg='blue',command=self.next_command)
        self.B2.pack(side=LEFT)
        self.flag=0
        self.track=0
        self.pg=0
        self.pagecond='notlast'

    def initialize(self):
        global path
        init_cond1='Please wait while the search engine performs the initialization phase:'
        self.T2.insert(END,init_cond1+'\n')
        status=[' ( Pending...)',' ( In progress... )',' ( Completed )']
        actions=[' Loading Paper Metadata',' Loading Citation data',' Computing PageRank Scores']
        for item in actions:
            self.T2.insert(END,item+status[0]+'\n')
        self.T2.delete('2.0','3.0')
        self.T2.insert('2.0',actions[0]+status[1]+'\n')
        self.T2.update()
        self.dataFetch=DataFetcher(path)
        self.dataFetch.paperdata_loader()
        self.T2.delete('2.0','3.0')
        self.T2.insert('2.0',actions[0]+status[2]+'\n')
        self.T2.delete('3.0','4.0')
        self.T2.insert('3.0',actions[1]+status[1]+'\n')
        self.T2.update()
        self.dataFetch.citation_data_loader()
        self.T2.delete('3.0','4.0')
        self.T2.insert('3.0',actions[1]+status[2]+'\n')
        self.T2.delete('4.0','5.0')
        self.T2.insert('4.0',actions[2]+status[1]+'\n')
        self.T2.update()
        self.dataFetch.pagerank_calculator()
        self.T2.delete('4.0','5.0')
        self.T2.insert('4.0',actions[2]+status[2]+'\n')
        self.T2.update()
        self.B1.config(text='Search')
        self.flag=1

    def search(self):
        try:
            start=timeit.default_timer()
            self.T2.delete('1.0',END)
            inpt=self.T1.get("1.0",'end-1c')
            self.dataFetch.content_based_calculator(inpt)
            self.dataFetch.almagamate()
            self.out=self.dataFetch.final_output()
            if len(inpt)>0:
                self.loc=1
                self.loc=self.loc+self.pg
                c=0
                self.track_list=[]
                self.rem=len(self.out)%20
                self.num_of_pages=len(self.out)/20
                if len(self.out)<=20:
                    loc=1
                    for tit,score in self.out:
                            score=str(score)[0:6]
                            self.T2.insert(END,'%d) '%loc+tit+' (%s)'%score+'\n')
                            loc+=1
                else:
                    for i in range(self.num_of_pages):
                        self.track_list.append((c,c+20))
                        c+=20
                    for i in range(len(self.track_list)):
                        if self.track==i:
                            for tit,score in self.out[self.track_list[i][0]:self.track_list[i][1]]:
                                score=str(score)[0:6]
                                self.T2.insert(END,'%d) '%self.loc+tit+' (%s)'%score+'\n')
                                self.loc+=1
                stop=timeit.default_timer()
                tt=str(stop - start)[0:6]
                self.L3.config(text='%d Papers [%s seconds]'%(len(self.out),tt))
            else:
                self.T2.delete('1.0',END)
                self.T2.insert(END,'No results found...')
        except:
            self.T2.delete('1.0',END)
            self.T2.insert(END,'No results Found...')
            raise AttributeError

    def reset_all(self):
        self.track=0
        self.pg=0
        self.pagecond='notlast'
        self.loc=1
        self.L2.config(text='1')
        self.L3.config(text='0 papers')

    def next_command(self):
        if self.track<self.num_of_pages-1:
            self.track+=1
            self.pg+=20
            self.search()
            self.L2.config(text='%d'%(self.track+1))
        elif self.track==self.num_of_pages-1:
            self.T2.delete('1.0',END)
            for tit,score in self.out[self.track_list[-1][1]:self.track_list[-1][1]+self.rem]:
                score=str(score)[0:6]
                self.T2.insert(END,'%d) '%self.loc+tit+' (%s)'%score+'\n')
                self.loc+=1
            self.track+=1
            self.L2.config(text='%d'%(self.track+1))
            self.pagecond='last'
        else:
            pass

    def prev_command(self):
        if self.track>0 and self.pagecond is not 'last':
            self.track-=1
            self.pg-=20
            self.search()
            self.L2.config(text='%d'%(self.track+1))
        elif self.pagecond is 'last':
            self.T2.delete('1.0',END)
            self.loc-=(20+self.rem)
            for tit,score in self.out[self.track_list[-1][0]:self.track_list[-1][1]]:
                score=str(score)[0:6]
                self.T2.insert(END,'%d) '%self.loc+tit+' (%s)'%score+'\n')
                self.loc+=1
            self.track-=1
            self.L2.config(text='%d'%(self.track+1))
            self.pagecond='notlast'

    def init_search(self):
        if self.flag==0:
            self.initialize()
        else:
            self.reset_all()
            self.search()










root = Tk()
app = App(root)
root.mainloop()
