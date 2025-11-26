// landmarks.js - 城市地标数据文件
const cityLandmarks = {
    'shanghai': [
        // 市中心区域
        { id: 'sh-1', name: '人民广场', x: 550, y: 475, icon: 'bi-star-fill', type: 'center' },
        { id: 'sh-3', name: '徐家汇', x: 509, y: 536, icon: 'bi-shop', type: 'commercial' },
        { id: 'sh-4', name: '外滩', x: 567, y: 474, icon: 'bi-water', type: 'scenic' },
        { id: 'sh-5', name: '虹桥机场', x: 401, y: 524, icon: 'bi-airplane', type: 'transport' },
        { id: 'sh-6', name: '浦东机场', x: 920, y: 594, icon: 'bi-airplane-fill', type: 'transport' },
        { id: 'sh-7', name: '静安寺', x: 533, y: 488, icon: 'bi-house', type: 'historic' },
        { id: 'sh-8', name: '上海火车站', x: 530, y: 455, icon: 'bi-train-front', type: 'transport' },
        { id: 'sh-9', name: '豫园', x: 566, y: 481, icon: 'bi-tree-fill', type: 'scenic' },
        { id: 'sh-11', name: '南京路步行街', x: 551, y: 472, icon: 'bi-shop-window', type: 'commercial' },
        
        
        { id: 'sh-12', name: '上海科技馆', x: 627, y: 500, icon: 'bi-bank2', type: 'culture' },
        { id: 'sh-13', name: '世纪公园', x: 641, y: 503, icon: 'bi-tree', type: 'park' },
        { id: 'sh-14', name: '上海野生动物园', x: 817, y: 707, icon: 'bi-emoji-laughing', type: 'park' },
        { id: 'sh-15', name: '上海迪士尼', x: 756, y: 594, icon: 'bi-stars', type: 'culture' },
        { id: 'sh-16', name: '松江大学城', x: 285, y: 712, icon: 'bi-book', type: 'education' },
        { id: 'sh-17', name: '佘山', x: 242, y: 638, icon: 'bi-geo-fill', type: 'scenic' },
        { id: 'sh-18', name: '朱家角古镇', x: 64, y: 620, icon: 'bi-house-door', type: 'historic' },
        { id: 'sh-19', name: '上海体育场', x: 513, y: 542, icon: 'bi-dribbble', type: 'culture' },
        { id: 'sh-20', name: '五角场', x: 576, y: 380, icon: 'bi-shop', type: 'commercial' },
        { id: 'sh-21', name: '上海海洋水族馆', x: 588, y: 470, icon: 'bi-water', type: 'culture' },
        { id: 'sh-22', name: '复旦大学', x: 580, y: 391, icon: 'bi-mortarboard-fill', type: 'education' },
        { id: 'sh-23', name: '交通大学', x: 511, y: 745, icon: 'bi-mortarboard', type: 'education' },
        { id: 'sh-24', name: '中山公园', x: 476, y: 510, icon: 'bi-tree', type: 'park' },
        { id: 'sh-25', name: '上海大剧院', x: 539, y: 474, icon: 'bi-music-note', type: 'culture' }
    ],
    'beijing': [
        // 市中心区域
        { id: 'bj-1', name: '天安门', x: 515, y: 511, icon: 'bi-star-fill', type: 'center' },
        { id: 'bj-2', name: '故宫', x: 515, y: 488, icon: 'bi-house', type: 'historic' },
        { id: 'bj-3', name: '颐和园', x: 244, y: 273, icon: 'bi-tree', type: 'scenic' },
        { id: 'bj-4', name: '天坛', x: 545, y: 597, icon: 'bi-circle', type: 'historic' },
        { id: 'bj-5', name: '王府井', x: 544, y: 511, icon: 'bi-shop', type: 'commercial' },
        { id: 'bj-6', name: '北京首都机场', x: 968, y: 26, icon: 'bi-airplane-fill', type: 'transport' },
        { id: 'bj-7', name: '北京西站', x: 344, y: 561, icon: 'bi-train-front', type: 'transport' },
        { id: 'bj-9', name: '奥林匹克公园', x: 505, y: 233, icon: 'bi-dribbble', type: 'culture' },
        { id: 'bj-10', name: '什刹海', x: 487, y: 432, icon: 'bi-water', type: 'scenic' },
        { id: 'bj-11', name: '中关村', x: 344, y: 300, icon: 'bi-buildings', type: 'industry' },
        { id: 'bj-12', name: '后海', x: 487, y: 428, icon: 'bi-water', type: 'culture' },
        { id: 'bj-13', name: '三里屯', x: 650, y: 437, icon: 'bi-cup-straw', type: 'culture' },
        { id: 'bj-14', name: '798艺术区', x: 738, y: 299, icon: 'bi-palette', type: 'culture' },
        { id: 'bj-15', name: '北京大学', x: 319, y: 290, icon: 'bi-mortarboard-fill', type: 'education' },
        { id: 'bj-16', name: '清华大学', x: 358, y: 262, icon: 'bi-mortarboard', type: 'education' },
        { id: 'bj-17', name: '南锣鼓巷', x: 531, y: 437, icon: 'bi-house-door', type: 'historic' },
        { id: 'bj-18', name: '北京动物园', x: 385, y: 422, icon: 'bi-emoji-smile', type: 'park' },
        { id: 'bj-19', name: '北京南站', x: 472, y: 648, icon: 'bi-train-front', type: 'transport' },
        { id: 'bj-21', name: '鸟巢', x: 515, y: 390, icon: 'bi-geo-alt-fill', type: 'culture' },
        { id: 'bj-23', name: '香山', x: 112, y: 302, icon: 'bi-tree-fill', type: 'scenic' },
        { id: 'bj-24', name: 'CBD商圈', x: 641, y: 532, icon: 'bi-building-fill', type: 'commercial' },
        { id: 'bj-25', name: '前门大街', x: 526, y: 555, icon: 'bi-signpost-2', type: 'commercial' }
    ],
    'guangzhou': [
        // 市中心区域
        { id: 'gz-1', name: '珠江新城', x: 998, y: 313, icon: 'bi-building', type: 'commercial' },
        { id: 'gz-4', name: '广州塔', x: 998, y: 401, icon: 'bi-broadcast-pin', type: 'scenic' },
        { id: 'gz-5', name: '北京路', x: 783, y: 325, icon: 'bi-shop', type: 'commercial' },
        { id: 'gz-6', name: '广州火车站', x: 734, y: 189, icon: 'bi-train-front', type: 'transport' },
        { id: 'gz-7', name: '沙面岛', x: 678, y: 386, icon: 'bi-water', type: 'historic' },
        { id: 'gz-8', name: '陈家祠', x: 686, y: 293, icon: 'bi-house', type: 'historic' },
        { id: 'gz-9', name: '白云山', x: 873, y: 43, icon: 'bi-geo-fill', type: 'scenic' },
        { id: 'gz-10', name: '越秀公园', x: 768, y: 221, icon: 'bi-tree', type: 'park' },
        { id: 'gz-13', name: '上下九步行街', x: 700, y: 343, icon: 'bi-shop-window', type: 'commercial' },
        { id: 'gz-14', name: '广州南站', x: 786, y: 957, icon: 'bi-train-front', type: 'transport' },
        { id: 'gz-16', name: '广州动物园', x: 945, y: 229, icon: 'bi-emoji-smile', type: 'park' },
        { id: 'gz-19', name: '长隆欢乐世界', x: 987, y: 914, icon: 'bi-emoji-laughing', type: 'culture' },
    ],
    'shenzhen': [
        { id: 'sz-2', name: '深圳湾', x: 201, y: 959, icon: 'bi-water', type: 'scenic' },
        { id: 'sz-4', name: '世界之窗', x: 209, y: 891, icon: 'bi-hexagon2', type: 'culture' },
        { id: 'sz-5', name: '华强北', x: 710, y: 854, icon: 'bi-pc-display', type: 'commercial' },
        { id: 'sz-6', name: '深圳北站', x: 453, y: 532, icon: 'bi-train-front', type: 'transport' },
        { id: 'sz-9', name: '东门步行街', x: 849, y: 832, icon: 'bi-shop-window', type: 'commercial' },
        { id: 'sz-10', name: '深圳大学', x: 41, y: 895, icon: 'bi-mortarboard', type: 'education' },
        { id: 'sz-11', name: '欢乐谷', x: 231, y: 863, icon: 'bi-emoji-laughing', type: 'culture' },
        { id: 'sz-12', name: '深圳湾体育中心', x: 102, y: 970, icon: 'bi-dribbble', type: 'culture' },
        { id: 'sz-16', name: '深圳书城', x: 586, y: 834, icon: 'bi-book', type: 'culture' },
        { id: 'sz-17', name: '红树林', x: 509, y: 150, icon: 'bi-tree-fill', type: 'park' },
        { id: 'sz-18', name: '罗湖口岸', x: 848, y: 921, icon: 'bi-signpost-split', type: 'transport' },
        { id: 'sz-19', name: '莲花山公园', x: 580, y: 788, icon: 'bi-tree', type: 'park' },
        { id: 'sz-20', name: '腾讯总部', x: 33, y: 860, icon: 'bi-buildings', type: 'industry' }
    ],
    'hangzhou': [
        { id: 'hz-1', name: '西湖', x: 267, y: 483, icon: 'bi-water', type: 'scenic' },
        { id: 'hz-2', name: '西溪湿地', x: 61, y: 476, icon: 'bi-water', type: 'park' },
        { id: 'hz-3', name: '阿里巴巴', x: 347, y: 649, icon: 'bi-buildings', type: 'industry' },
        { id: 'hz-4', name: '杭州东站', x: 388, y: 393, icon: 'bi-train-front', type: 'transport' },
        { id: 'hz-5', name: '钱江新城', x: 390, y: 493, icon: 'bi-building-fill', type: 'commercial' },
        { id: 'hz-6', name: '灵隐寺', x: 141, y: 520, icon: 'bi-house', type: 'historic' },
        { id: 'hz-7', name: '浙江大学', x: 104, y: 360, icon: 'bi-mortarboard', type: 'education' },
        { id: 'hz-10', name: '湘湖', x: 404, y: 774, icon: 'bi-water', type: 'scenic' },
        { id: 'hz-12', name: '宋城', x: 133, y: 703, icon: 'bi-house-door', type: 'culture' },
        { id: 'hz-13', name: '京杭大运河', x: 229, y: 360, icon: 'bi-water', type: 'historic' },
        { id: 'hz-14', name: '西湖文化广场', x: 277, y: 429, icon: 'bi-music-note', type: 'culture' },
    ],
    'chengdu': [
        { id: 'cd-2', name: '宽窄巷子', x: 524, y: 488, icon: 'bi-shop-window', type: 'historic' },
        { id: 'cd-3', name: '成都大熊猫繁育基地', x: 889, y: 101, icon: 'bi-emoji-smile', type: 'park' },
        { id: 'cd-5', name: '春熙路', x: 605, y: 582, icon: 'bi-shop', type: 'commercial' },
        { id: 'cd-6', name: '成都东站', x: 901, y: 675, icon: 'bi-train-front', type: 'transport' },
        { id: 'cd-8', name: '杜甫草堂', x: 411, y: 506, icon: 'bi-house', type: 'historic' },
        { id: 'cd-9', name: '武侯祠', x: 485, y: 582, icon: 'bi-house-door', type: 'historic' },
        { id: 'cd-10', name: '天府广场', x: 500, y: 500, icon: 'bi-star-fill', type: 'center' },
        { id: 'cd-11', name: '成都双流机场', x: 67, y: 963, icon: 'bi-airplane-fill', type: 'transport' },
        { id: 'cd-12', name: '四川大学', x: 651, y: 662, icon: 'bi-mortarboard', type: 'education' },
        { id: 'cd-14', name: 'IFS国际金融中心', x: 634, y: 539, icon: 'bi-building-fill', type: 'commercial' },
        { id: 'cd-15', name: '环球中心', x: 556, y: 984, icon: 'bi-hexagon', type: 'commercial' }
    ],
    'shenyang': [
        // 政府部门
        { id: 'sy-25', name: '沈阳市政府', x: 610, y: 834, icon: 'bi-buildings', type: 'center' },
        { id: 'sy-26', name: '辽宁省政府', x: 536, y: 365, icon: 'bi-buildings', type: 'center' },

        // 市中心区域
        { id: 'sy-1', name: '沈河区中街', x: 613, y: 460, icon: 'bi-shop-window', type: 'commercial' },
        { id: 'sy-2', name: '和平区太原街', x: 475, y: 490, icon: 'bi-shop', type: 'commercial' },
        { id: 'sy-3', name: '铁西区兴华街', x: 400, y: 498, icon: 'bi-building', type: 'commercial' },
        { id: 'sy-4', name: '皇姑区黄河大街', x: 515, y: 417, icon: 'bi-building', type: 'commercial' },
        
        // 交通枢纽
        { id: 'sy-5', name: '桃仙国际机场', x: 663, y: 958, icon: 'bi-airplane-fill', type: 'transport' },
        { id: 'sy-6', name: '沈阳北站', x: 547, y: 418, icon: 'bi-train-front', type: 'transport' },
        { id: 'sy-7', name: '沈阳站', x: 450, y: 487, icon: 'bi-train-front', type: 'transport' },
        { id: 'sy-7', name: '沈阳南站', x: 479, y: 866, icon: 'bi-train-front', type: 'transport' },
        { id: 'sy-23', name: '沈阳浑河大桥', x: 570, y: 619, icon: 'bi-signpost-split', type: 'transport' },
        
        // 历史古迹
        { id: 'sy-8', name: '沈阳故宫', x: 603, y: 472, icon: 'bi-house', type: 'historic' },
        { id: 'sy-10', name: '张氏帅府', x: 609, y: 487, icon: 'bi-house-door', type: 'historic' },
        
        // 教育机构
        { id: 'sy-11', name: '辽宁大学', x: 492, y: 372, icon: 'bi-mortarboard', type: 'education' },
        { id: 'sy-12', name: '东北大学', x: 518, y: 908, icon: 'bi-mortarboard-fill', type: 'education' },
        { id: 'sy-13', name: '沈阳工业大学', x: 135, y: 657, icon: 'bi-mortarboard', type: 'education' },
        
        // 文化场所
        { id: 'sy-14', name: '辽宁省博物馆', x: 600, y: 834, icon: 'bi-bank', type: 'culture' },
        { id: 'sy-15', name: '沈阳奥体中心', x: 606, y: 646, icon: 'bi-dribbble', type: 'culture' },
        { id: 'sy-19', name: '沈阳方特欢乐世界', x:487, y: 1, icon: 'bi-emoji-laughing', type: 'culture' },
        { id: 'sy-21', name: '辽宁大剧院', x: 552, y: 451, icon: 'bi-music-note', type: 'culture' },
        
        // 公园绿地
        { id: 'sy-9', name: '北陵公园', x: 534, y: 340, icon: 'bi-tree-fill', type: 'park' },
        { id: 'sy-24', name: '沈阳南湖公园', x: 502, y: 565, icon: 'bi-water', type: 'park' },
        
        // 景点名胜  
        { id: 'sy-27', name: '鸟岛', x: 925, y: 397, icon: 'bi-geo-alt-fill', type: 'scenic' },

        // 产业园区
        { id: 'sy-28', name: '东软软件园', x: 543, y: 761, icon: 'bi-buildings', type: 'industry' },
    ],
    'chongqing': [
        { id: 'cq-2', name: '洪崖洞', x: 894, y: 367, icon: 'bi-house-door', type: 'scenic' },
        { id: 'cq-3', name: '朝天门', x: 936, y: 338, icon: 'bi-water', type: 'scenic' },
        { id: 'cq-5', name: '重庆北站', x: 768, y: 120, icon: 'bi-train-front', type: 'transport' },
        { id: 'cq-6', name: '观音桥', x: 692, y: 292, icon: 'bi-shop-window', type: 'commercial' },
        { id: 'cq-8', name: '磁器口古镇', x: 322, y: 261, icon: 'bi-house', type: 'historic' },
        { id: 'cq-9', name: '重庆大学', x: 424, y: 354, icon: 'bi-mortarboard-fill', type: 'education' },
        { id: 'cq-10', name: '重庆三峡博物馆', x: 772, y: 356, icon: 'bi-bank', type: 'culture' },
        { id: 'cq-11', name: '长江索道', x: 926, y: 395, icon: 'bi-signpost-split', type: 'transport' },
        { id: 'cq-13', name: '南滨路', x: 885, y: 466, icon: 'bi-water', type: 'scenic' },
        { id: 'cq-14', name: '白象居', x: 926, y: 392, icon: 'bi-shop', type: 'commercial' },
        { id: 'cq-15', name: '山城步道', x: 841, y: 422, icon: 'bi-signpost', type: 'scenic' },
        { id: 'cq-16', name: '重庆科技馆', x: 886, y: 315, icon: 'bi-building', type: 'culture' },
        { id: 'cq-17', name: '歌乐山烈士陵园', x: 293, y: 311, icon: 'bi-geo-fill', type: 'historic' },
        { id: 'cq-19', name: '江北嘴中央商务区', x: 848, y: 315, icon: 'bi-building-fill', type: 'commercial' },
        { id: 'cq-20', name: '重庆美术馆', x: 889, y: 376, icon: 'bi-palette', type: 'culture' },
        { id: 'cq-21', name: '鹅岭公园', x: 708, y: 423, icon: 'bi-tree', type: 'park' },


    ],
    'wuhan': [
        { id: 'wh-1', name: '武汉长江大桥', x: 431, y: 619, icon: 'bi-signpost-split', type: 'transport' },
        { id: 'wh-2', name: '黄鹤楼', x: 461, y: 636, icon: 'bi-building', type: 'historic' },
        { id: 'wh-3', name: '东湖', x: 697, y: 611, icon: 'bi-water', type: 'scenic' },
        { id: 'wh-4', name: '武汉天河国际机场', x: 282, y: 46, icon: 'bi-airplane-fill', type: 'transport' },
        { id: 'wh-5', name: '汉口江滩', x: 496, y: 466, icon: 'bi-water', type: 'scenic' },
        { id: 'wh-6', name: '武汉大学', x: 605, y: 651, icon: 'bi-mortarboard-fill', type: 'education' },
        { id: 'wh-7', name: '华中科技大学', x: 722, y: 706, icon: 'bi-mortarboard', type: 'education' },
        { id: 'wh-8', name: '归元寺', x: 375, y: 630, icon: 'bi-house', type: 'historic' },
        { id: 'wh-9', name: '江汉路步行街', x: 432, y: 527, icon: 'bi-shop-window', type: 'commercial' },
        { id: 'wh-10', name: '光谷广场', x: 684, y: 733, icon: 'bi-building-fill', type: 'commercial' },
        { id: 'wh-11', name: '户部巷', x: 452, y: 620, icon: 'bi-shop', type: 'commercial' },
        { id: 'wh-12', name: '武汉站', x: 732, y: 471, icon: 'bi-train-front', type: 'transport' },
        { id: 'wh-13', name: '武昌站', x: 495, y: 673, icon: 'bi-train-front', type: 'transport' },
        { id: 'wh-14', name: '汉口站', x: 356, y: 441, icon: 'bi-train-front', type: 'transport' },
        { id: 'wh-15', name: '楚河汉街', x: 560, y: 608, icon: 'bi-shop', type: 'commercial' },
        { id: 'wh-16', name: '中山公园', x: 391, y: 522, icon: 'bi-tree', type: 'park' },
        { id: 'wh-17', name: '武汉科技馆', x: 454, y: 542, icon: 'bi-building', type: 'culture' },
        { id: 'wh-18', name: '武汉长江二桥', x: 514, y: 481, icon: 'bi-signpost-split', type: 'transport' },
        { id: 'wh-20', name: '武汉革命博物馆', x: 461, y: 607, icon: 'bi-bank', type: 'culture' },

    ],
    'xian': [
        { id: 'xa-2', name: '大雁塔', x: 544, y: 663, icon: 'bi-building', type: 'historic' },
        { id: 'xa-3', name: '西安古城墙', x: 510, y: 507, icon: 'bi-bricks', type: 'historic' },
        { id: 'xa-5', name: '鼓楼', x: 496, y: 550, icon: 'bi-building', type: 'historic' },
        { id: 'xa-6', name: '回民街', x: 498, y: 555, icon: 'bi-shop', type: 'commercial' },
        { id: 'xa-7', name: '西安咸阳国际机场', x: 110, y: 68, icon: 'bi-airplane-fill', type: 'transport' },
        { id: 'xa-8', name: '陕西历史博物馆', x: 527, y: 643, icon: 'bi-bank', type: 'culture' },
        { id: 'xa-9', name: '大唐芙蓉园', x: 569, y: 690, icon: 'bi-tree-fill', type: 'park' },
        { id: 'xa-10', name: '西安火车站', x: 542, y: 511, icon: 'bi-train-front', type: 'transport' },
        { id: 'xa-12', name: '小雁塔', x: 495, y: 615, icon: 'bi-building', type: 'historic' },
        { id: 'xa-13', name: '曲江池遗址公园', x: 577, y: 707, icon: 'bi-water', type: 'park' },
        { id: 'xa-14', name: '西安北站', x: 488, y: 247, icon: 'bi-train-front', type: 'transport' },
        { id: 'xa-15', name: '大明宫国家遗址公园', x: 541, y: 473, icon: 'bi-geo-fill', type: 'historic' },
        { id: 'xa-16', name: '西安交通大学', x: 588, y: 592, icon: 'bi-mortarboard-fill', type: 'education' },
        { id: 'xa-17', name: '西北工业大学', x: 437, y: 606, icon: 'bi-mortarboard', type: 'education' },



    ],
    'nanjing': [
        
        // 交通枢纽
        { id: 'nj-7', name: '南京南站', x: 486, y: 736, icon: 'bi-train-front', type: 'transport' },
        { id: 'nj-8', name: '南京站', x: 487, y: 427, icon: 'bi-train-front', type: 'transport' },

        
        // 历史古迹
        { id: 'nj-11', name: '中山陵', x: 609, y: 516, icon: 'bi-house', type: 'historic' },
        { id: 'nj-12', name: '夫子庙', x: 467, y: 593, icon: 'bi-house-door', type: 'historic' },
        { id: 'nj-13', name: '明孝陵', x: 577, y: 519, icon: 'bi-geo-alt-fill', type: 'historic' },
        { id: 'nj-14', name: '南京总统府', x: 482, y: 539, icon: 'bi-building', type: 'historic' },
        
        // 教育机构
        { id: 'nj-18', name: '南京大学', x: 444, y: 509, icon: 'bi-mortarboard-fill', type: 'education' },
        { id: 'nj-19', name: '东南大学', x: 537, y: 949, icon: 'bi-mortarboard', type: 'education' },


        
        // 景点
        { id: 'nj-24', name: '玄武湖', x: 500, y: 473, icon: 'bi-water', type: 'scenic' },
        { id: 'nj-25', name: '栖霞山', x: 870, y: 236, icon: 'bi-geo-fill', type: 'scenic' },
        { id: 'nj-26', name: '紫金山', x: 608, y: 484, icon: 'bi-geo-fill', type: 'scenic' },
        { id: 'nj-27', name: '莫愁湖', x: 409, y: 501, icon: 'bi-water', type: 'scenic' },
        { id: 'nj-28', name: '秦淮河', x: 477, y: 601, icon: 'bi-water', type: 'scenic' },
        { id: 'nj-29', name: '牛首山', x: 370, y: 878, icon: 'bi-geo-fill', type: 'scenic' },
        
        // 文化场所
        { id: 'nj-30', name: '南京博物院', x: 546, y: 547, icon: 'bi-bank', type: 'culture' },
        { id: 'nj-31', name: '南京图书馆', x: 482, y: 543, icon: 'bi-book', type: 'culture' },
        { id: 'nj-32', name: '江苏大剧院', x: 300, y: 625, icon: 'bi-music-note', type: 'culture' },

        // 公园
        { id: 'nj-36', name: '梅花山', x: 584, y: 522, icon: 'bi-flower1', type: 'park' },
        { id: 'nj-37', name: '白鹭洲公园', x:480, y: 608, icon: 'bi-tree-fill', type: 'park' },
        { id: 'nj-38', name: '红山森林动物园', x: 498, y: 416, icon: 'bi-emoji-smile', type: 'park' },

        
        // 商业区
        { id: 'nj-40', name: '湖南路', x: 432, y: 471, icon: 'bi-shop', type: 'commercial' },
        { id: 'nj-41', name: '珠江路', x: 480, y: 526, icon: 'bi-shop', type: 'commercial' },
    
        
        // 产业园区
        { id: 'nj-45', name: '南京软件园', x: 263, y: 259, icon: 'bi-buildings', type: 'industry' },

    ]
};

// 导出地标数据
if (typeof module !== 'undefined' && module.exports) {
    module.exports = cityLandmarks;
} 