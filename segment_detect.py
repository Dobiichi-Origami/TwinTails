# -*- coding:utf-8 -*-

from pyhanlp import *
import math

CoNLLSentence = JClass('com.hankcs.hanlp.corpus.dependency.CoNll.CoNLLSentence')
CoNLLWord = JClass('com.hankcs.hanlp.corpus.dependency.CoNll.CoNLLWord')

# 神经网络词法分析器
IDependencyParser = JClass('com.hankcs.hanlp.dependency.IDependencyParser')
NeuralNetworkDependencyParser = JClass('com.hankcs.hanlp.dependency.nnparser.NeuralNetworkDependencyParser')

# 结构化感知机相关
PerceptronSegmenter = JClass('com.hankcs.hanlp.model.perceptron.PerceptronSegmenter')
POSTrainer = JClass('com.hankcs.hanlp.model.perceptron.POSTrainer')
NERTrainer = JClass('com.hankcs.hanlp.model.perceptron.NERTrainer')

# word2vec
WordVectorModel = JClass('com.hankcs.hanlp.mining.word2vec.WordVectorModel')
Vector = JClass('com.hankcs.hanlp.mining.word2vec.Vector')

nounSet = {'an', 'j', 'mg', 'm', 'ng', 'n', 'nr', 'ns', 'nt', 'nx', 'nz', 'q', 'rg', 'r', 'vn', 'nrj', 'nrf', 'nsf', 'ntc',
           'ntcf', 'ntcb', 'ntch', 'nto', 'ntu', 'nts', 'nth', 'nh', 'nhm', 'nhd', 'nn', 'nnt', 'nnd', 'ni', 'nic', 'nis',
           'nm', 'nmc', 'nb', 'nba', 'nbp', 'g', 'gm', 'gp', 'gc', 'gb', 'gbc', 'gg', 'gi', 'rr', 'x', 'nr1', 'nr2', 'nf',
           'nit', 'nbc', 'nl', 'i', 'a'}

verbSet = {'v', 'vshi', 'vyou', 'vi', 'vf', 'vx', 'vd', 'vl', 'vg', 'd'}

model = WordVectorModel('word2vecModel/hanlp-wiki-vec-zh.txt')
segmenter = PerceptronSegmenter('structed_model/model')
analyzer = PerceptronLexicalAnalyzer('structed_model/model',
                                     'structed_model/posmodel',
                                     'structed_model/nermodel')
parser = NeuralNetworkDependencyParser(analyzer)


# 相似度树的节点结构，保存了到父节点的依存语法关系名称和子节点数组
class Node:
    def __init__(self, relation: str):
        self.children = []
        self.relation = relation


# 相似度树，保存了核心节点，使用迭代的方式从依存语法树中抽取公有结构
class SimilarityTree:
    def __init__(self, index1, index2, arr1, arr2, relationArr1, relationArr2):
        self.root = Node("核心关系")
        flag = []
        for i in range(0, len(relationArr2)):
            flag.append(0)
        self.generateSimilarityTree(index1, index2, arr1, arr2, relationArr1, relationArr2, flag, self.root)

    def generateSimilarityTree(self, index1, index2, arr1, arr2, relationArr1, relationArr2, flag, nodeNow: Node):
        # 这个方法无法保证一定抽取出最大公共子结构，有待改进
        for i in range(0, len(arr1[index1])):
            if arr1[index1][i] == 0:
                continue
            for j in range(0, len(arr2[index2])):
                if arr2[index2][j] == 0:
                    continue
                if flag[j] == 0 and relationArr1[i].DEPREL == relationArr2[j].DEPREL:
                    flag[j] = 1
                    node = Node(relationArr1[i].DEPREL)
                    nodeNow.children.append(node)
                    self.generateSimilarityTree(i, j, arr1, arr2, relationArr1, relationArr2, flag, node)
                    break

    def printToConsole(self):
        self.iterateForPrint(self.root)

    def iterateForPrint(self, nodeNow: Node):
        print(nodeNow.relation)
        for i in range(0, len(nodeNow.children)):
            self.iterateForPrint(nodeNow.children[i])

    def getDepth(self):
        return self.iterateForDepth(self.root)

    def iterateForDepth(self, nodeNow: Node):
        sumx = 0
        for i in range(0, len(nodeNow.children)):
            sumx = max(sumx, self.iterateForDepth(nodeNow.children[i]))
        return sumx + 1

    def getLength(self, depth):
        return self.iterateForLength(self.root, depth)

    def iterateForLength(self, nodeNow: Node, depth: int):
        sumx = 0
        for i in range(0, len(nodeNow.children)):
            sumx += self.iterateForLength(nodeNow.children[i], depth-1)
        sumx += len(nodeNow.children) * depth
        return depth if sumx == 0 else sumx


# 生成指定行数和列数的二维数组
def initialArr(row, column):
    arr = []
    for i in range(0, row):
        temp = []
        for j in range(0, column):
            temp.append(0)
        arr.append(temp)
    return arr


# 生成指定长度的一维数组
def initialArr1D(length):
    arr = []
    for i in range(0, length):
        arr.append(0)

    return arr


# 生成依存语法树的邻接矩阵表达形式
def generateAdjacencyMatrix(tree_arr):
    arr = initialArr(len(tree_arr), len(tree_arr))
    for i in range(0, len(tree_arr)):
        for j in range(0, len(tree_arr)):
            if i == j:
                continue
            if tree_arr[j].HEAD == tree_arr[i]:
                arr[i][j] = 1
    return arr


# 获取核心关系所指代的词汇索引
def getCoretext(tree_arr):
    for i in range(0, len(tree_arr)):
        if CoNLLWord.ROOT == tree_arr[i].HEAD:
            return i


# 根据依存语法关系获取相似树
def getSimilarityTree(word_arr1, word_arr2):
    index1 = getCoretext(word_arr1)
    index2 = getCoretext(word_arr2)
    arr1 = generateAdjacencyMatrix(word_arr1)
    arr2 = generateAdjacencyMatrix(word_arr2)
    return SimilarityTree(index1, index2, arr1, arr2, word_arr1, word_arr2)


# 计算两棵依存语法树的相似度
def getSimilarityOfSentenceFromTree(sentence1, sentence2):
    word_arr1 = parser.parse(sentence1).getWordArray()
    word_arr2 = parser.parse(sentence2).getWordArray()

    tree1 = getSimilarityTree(word_arr1, word_arr1)
    tree2 = getSimilarityTree(word_arr2, word_arr2)
    similarTree = getSimilarityTree(word_arr1, word_arr2)
    similarity1 = float(similarTree.getLength(tree1.getDepth())) / float(tree1.getLength(tree1.getDepth()))
    similarity2 = float(similarTree.getLength(tree2.getDepth())) / float(tree2.getLength(tree2.getDepth()))
    return [similarity1, similarity2]


# 获取分词结果中的名词
def getNounWords(arr):
    ans = []
    for term in arr:
        if term.nature.toString() in nounSet:
            ans.append(term.word)
    return ans


# 获取分词结果中的动词
def getVerbWord(arr):
    ans = []
    for term in arr:
        if term.nature.toString() in verbSet:
            ans.append(term.word)
    return ans


# 组装完整的名词
def getWholeNoun(CoSentence, i):
    noun = CoSentence.word[i].LEMMA

    for j in range(1, i + 1):
        if CoSentence.word[i - j].POSTAG.lower() in nounSet or CoSentence.word[i - j].LEMMA == "的" or CoSentence.word[i - j].CPOSTAG.lower() in nounSet:
            temp = CoSentence.word[i - j].LEMMA
            noun = temp + noun
        else:
            break
    for j in range(1, len(CoSentence.word) - i):
        if CoSentence.word[i + j].POSTAG.lower() in nounSet or CoSentence.word[i + j].LEMMA == "的" or CoSentence.word[i + j].CPOSTAG.lower() in nounSet:
            noun += CoSentence.word[i + j].LEMMA
        else:
            break

    return noun


# 组装完整的动词
def getWholeVerb(CoSentence, i):
    verb = CoSentence.word[i].LEMMA

    for j in range(1, i + 1):
        if CoSentence.word[i - j].POSTAG.lower() in verbSet or CoSentence.word[i - j].CPOSTAG.lower() in verbSet:
            temp = CoSentence.word[i - j].LEMMA
            verb = temp + verb
        else:
            break

    for j in range(1, len(CoSentence.word) - i):
        if CoSentence.word[i + j].POSTAG.lower() in verbSet or CoSentence.word[i + j].CPOSTAG.lower() in verbSet:
            verb += CoSentence.word[i + j].LEMMA
        else:
            break

    return verb


# 抽取三元组
def extractTripleTuple(CoSentence):
    triple = [set(), set(), set()]
    for i in range(0, len(CoSentence.word)):
        if CoSentence.word[i].DEPREL == "主谓关系":
            triple[0].add(getWholeNoun(CoSentence, i))
            triple[1].add(getWholeVerb(CoSentence, CoSentence.word[i].HEAD.ID - 1))

        if "宾关系" in CoSentence.word[i].DEPREL and CoSentence.word[i].POSTAG in nounSet:
            triple[2].add(getWholeNoun(CoSentence, i))

    for i in range(0, len(CoSentence.word)):
        if CoSentence.word[i].DEPREL == "并列关系":
            if CoSentence.word[i].HEAD.DEPREL == "主谓关系":
                triple[0].add(getWholeNoun(CoSentence, i))
            else:
                triple[2].add(getWholeNoun(CoSentence, i))

    return (list(triple[0]), list(triple[1]), list(triple[2]))


# 切分字符串
def divideString(answer: str):
    return answer.split(sep='。')


# 抽取出所有未被加工过的动词和名词
def extractOriginalVerbAndNoun(CoSentence):
    verbAndNoun = [[], []]

    for i in range(0, len(CoSentence.word)):
        if CoSentence.word[i].POSTAG in verbSet or CoSentence.word[i].CPOSTAG in verbSet:
            verbAndNoun[0].append(CoSentence.word[i].LEMMA)
        elif CoSentence.word[i].POSTAG in nounSet or CoSentence.word[i].CPOSTAG in nounSet:
            verbAndNoun[1].append(CoSentence.word[i].LEMMA)

    return verbAndNoun


# 获得一个文段中未被加工过的所有动词和名词
def getAllVerbAndNounFromPara(para: str):
    return extractOriginalVerbAndNoun(parser.parse(para))


# 计算一堆同词性词汇的平均向量
def calculateMeanVector(word):
    if len(word) == 0:
        return Vector(300)

    vector = Vector(300)
    offset = 0
    i = 0

    while i < len(word):
        temp = model.vector(word[i])
        if temp is None:    # 可能我们的模型中不包含这个词汇，无法生成对应的词向量，这里特别判断，如果存在这个情况我们就将其向下拆分成多个词汇，直至只剩下单字，如果单字也不存在向量，则直接跳过。
            if len(word[i]) == 1:
                i += 1
                continue
            tempArr = segmenter.segment(word[i])
            if len(tempArr) == 1:
                for char in tempArr[0]:
                    word.append(char)
            else:
                for wordx in tempArr:
                    word.append(wordx)
            offset += 1
        else:
            vector = vector.add(temp)
        i += 1

    return vector.divideToSelf(float(len(word) - offset))


# 计算两个词汇数组的余弦相似度
def computeSimilarityOfWords(words1, words2):
    vector1 = calculateMeanVector(words1)
    vector2 = calculateMeanVector(words2)

    ans = vector1.cosine(vector2)

    return ans if not math.isnan(vector1.cosine(vector2)) else -1.0


# 获取两句话的词汇余弦相似度
def getSimilarityFromWords(str1, str2):
    words1 = getAllVerbAndNounFromPara(str1)
    words2 = getAllVerbAndNounFromPara(str2)

    return [computeSimilarityOfWords(words1[0], words2[0]), computeSimilarityOfWords(words1[1], words2[1])]


# 废弃
def findDifferentSentenceToMatch(indexCantBeMatch, sent, sentsToMatch):
    maximum = 0
    index = 0

    for i in range(0, len(sentsToMatch)):
        if i == indexCantBeMatch:
            continue

        similarityArr = getSimilarityOfSentenceFromTree(sent, sentsToMatch[i])
        if maximum < (similarityArr[0] + similarityArr[1]) / float(2):
            maximum = (similarityArr[0] + similarityArr[1]) / float(2)
            index = i

    return [maximum, index]


# 计算两个文段的平均语法相似度，按句匹配，参数1为学生答案，参数2为标准答案
def getAverageTreeSimilarityOfTwoSentences(para1, para2):
    sents1 = divideString(para1)[0: -1]
    sents2 = divideString(para2)[0: -1]

    indexArr1 = initialArr1D(len(sents1))
    maximumArr1 = initialArr1D(len(sents1))

    for i in range(0, len(sents1)):
        for j in range(0, len(sents2)):
            similarityArr = getSimilarityOfSentenceFromTree(sents1[i], sents2[j])
            if maximumArr1[i] < (similarityArr[0] + similarityArr[1]) / float(2):
                maximumArr1[i] = (similarityArr[0] + similarityArr[1]) / float(2)
                indexArr1[i] = j

    averageSimilarity = 0.0
    for num in maximumArr1:
        averageSimilarity += num

    return [indexArr1, averageSimilarity / len(maximumArr1)]


def calculateSimilarityOfTriple(indexArr, para1, para2):
    sents1 = divideString(para1)
    sents2 = divideString(para2)
    arrOfSimilarity = [0, 0, 0]

    for i in range(0, len(indexArr)):
        tuple1 = extractTripleTuple(parser.parse(sents1[i]))
        tuple2 = extractTripleTuple(parser.parse(sents2[indexArr[i]]))

        for j in range(0, 3):
            arrOfSimilarity[j] += computeSimilarityOfWords(tuple1[j], tuple2[j])

    for i in range(0, 3):
        arrOfSimilarity[i] /= len(indexArr)

    return arrOfSimilarity


def getScore(str1, str2):   # 参数一为学生答案，参数二为标准答案
    ans = 0

    arr = getSimilarityFromWords(str1, str2)
    arr2 = getAverageTreeSimilarityOfTwoSentences(str1, str2)
    arr3 = calculateSimilarityOfTriple(arr2[0], str1, str2)
    ans = (((arr[0] + 1) / 2.0) + ((arr[1] + 1) / 2.0) + arr2[1] + ((arr3[0] + 1) / 2.0) + ((arr3[1] + 1) / 2.0) + ((arr3[2] + 1) / 2.0)) / 6.0
    return ans


if __name__ == '__main__':
    # parser = NeuralNetworkDependencyParser()
    # sentence = parser.parse("徐先生还具体帮助他确定了把画雄鹰、松鼠和麻雀作为主攻目标。")
    # print(sentence)
    # for word in sentence.iterator():  # 通过dir()可以查看sentence的方法
    #     print("%s --(%s)--> %s" % (word.LEMMA, word.DEPREL, word.HEAD.LEMMA))
    # print()
    #
    # # 也可以直接拿到数组，任意顺序或逆序遍历
    # word_array = sentence.getWordArray()
    # for word in word_array:
    #     print("%s --(%s)--> %s" % (word.LEMMA, word.DEPREL, word.HEAD.LEMMA))
    # print("接下来遍历子树\n")
    #
    # # 还可以直接遍历子树，从某棵子树的某个节点一路遍历到虚根
    # CoNLLWord = JClass("com.hankcs.hanlp.corpus.dependency.CoNll.CoNLLWord")
    # head = word_array[12]
    # print("%s --(%s)--> " % (head.LEMMA, head.DEPREL))
    # while head.HEAD:
    #     head = head.HEAD
    #     if (head == CoNLLWord.ROOT):
    #         print(head.LEMMA)
    #     else:
    #         print("%s --(%s)--> " % (head.LEMMA, head.DEPREL))

    # # print(getSimilarityOfSentence("人工智能是一门新兴学科", "人工智能是一门新兴学科"))
    # print(parser.parse("伴随着世界的发展"))
    # print(extractTripleTuple(parser.parse("伴随着世界的发展")))
    # print(extractVerbAndNoun(parser.parse("伴随着世界的发展")))

    print(getScore("相互孤立的计算机在不同网络条件下相互通信所必须遵守的规则。", "协议是网络协议的简称，是通信计算机双方必须共同遵从的一组约定。为了使计算机双方之间能够建立连接，传输数据，网络通信的参与方必须遵循相同的规则，即网络协议。协议的具体体现即是连入网络的计算机必须要遵循一定的技术规范，实现硬件、软件、端口等的一系列功能标准，才能实现各方顺利无误地信息传输。"))