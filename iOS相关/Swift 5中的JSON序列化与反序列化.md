# JSON是什么

​	JSON，全称 JavaScript Object Notation，是一种十分轻量的数据交换格式，JSON 可以使用字符串来表示一个或多个完整的对象，在网络信息传输中有着得天独厚的优势（因为十分轻量所以传输所消耗的资源并不多）。在Swift中我们也可以使用 JSON 进行数据的序列化和反序列化。

​	Swift经过多次版本迭代，目前最新的实现是在4.0版本中加入的 Encodable & Decodable协议。本文将以这套协议介绍如何在 Swift 中实现  JSON 的序列化和反序列化。

# Codable 和自动编解码

​	Codable是集合了Encodable和Decodable的别称，使用Codable就可以使得自定义的类型同时实现Encodable和Decodable协议。在Swift中，只要你的自定义类型所包含的属性全部是可以被编解码的，那么你的自定义类就可以实现编解码。这些属性的类型包括了：

1. 标准库里面的类型，例如Double，Int，String等
2. Foundation库里面的类型，例如Data，Date，URL等
3. 遵守了 Encodable/Decodable 协议的自定义结构



​	以下代码展示了一种可能出现的编解码情况，其中的LandMark类型包括了上面提到的三种可编解码属性，其中的属性是可以被编解码的。

```swift
struct Coordinate: Codable {
    var latitude: Double
    var longitude: Double
}

struct Landmark: Codable {
    var name: String
    var foundingYear: Int
    var location: Coordinate
    
    var vantagePoints: [Coordinate]
    var metadata: [String: String]
    var website: URL?
}
```

​	同时，我们可以看到的是，上面的代码里还出现了数组、字典和可选类型。如果其中包含的多态类型是上述三种类型之一，那么它们也可以被编解码。

​	在我们的自定义类型声明实现了Codable之后，我们就可以调用一个JSONEncoder实例，使用其中的编码方法 `encode(value: Encodable)` 生成一个Data对象，这个Data对象就是包含了我们 JSON格式数据的数据对象，可以使用 `String(data: Data, encoding: String.Encoding)` 方法转换成字符串打印输出其中的内容。

# 单独调用 Encodable 或 Decodable

​	上面说到Codable是两者的集合，我们单独声明类型遵守 Encodable 或 Decodable 也是可以的，这样子我们的类型只能实现解码或者编码中的其中一项。

```swift
struct Landmark: Encodable {	//只实现了Encodabel，只可被编码；反之，只能被解码
    var name: String
    var foundingYear: Int
}
```

# 随心指定和组合你想要被编解码的属性

​	如果你不想把所有的属性都给编解码的话，Swift还给你提供了省心省力的方式去指定你想要编解码的属性：声明一个叫做 CodingKeys 枚举属性在类/结构体中，让它实现CodingKey这个协议，在其中按照你的属性名写入case即可，例如：

```swift
struct Coordinate: Codable {
    var latitude: Double
    var longitude: Double
}

struct Landmark: Codable {
    var name: String
    var foundingYear: Int
    
    var location: Coordinate = Coordinate(latitude: 1, longitude: 2)
    
    enum CodingKeys:String, CodingKey{
        case name = "nice"
        case foundingYear
    }
}
```

​	在上面的代码中，Swift在编解码Landmark这个结构体时，只会将name与foudingYear两项纳入编解码范围内，而不考虑location。此外，还有两个需要注意的点

1. 如果你想将属性名以不同的名字进行编解码，在case后面添加其对应的字符串的rawValue即可
2. 如果有不需要进行编解码的属性，请手动赋予默认值，否则会报错

# 自己手动进行编解码

​	如果觉得自动处理不能满足你的需要，那你还可以自己实现编解码的过程

​	在实现了Encodable协议的类中，实现函数 `encode(to encoder: Encoder) throws` ，在函数体内完成你的解码过程

​	作为参数传入的encoder，我们可以向它的container中添加我们想要的键值对，实现自定义编码规则，同时支持多个container嵌套，以实现层级结构。decode方面亦然，只需要实现 `init(from decoder: Decoder) throws`  即可。以下代码给出了手动编解码的实例

```swift
extension Coordinate: Encodable {
    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(latitude, forKey: .latitude)
        try container.encode(longitude, forKey: .longitude)
        
        var additionalInfo = container.nestedContainer(keyedBy: AdditionalInfoKeys.self, forKey: .additionalInfo)
        try additionalInfo.encode(elevation, forKey: .elevation)
    }
}
```



```swift
extension Coordinate: Decodable {
    init(from decoder: Decoder) throws {
        let values = try decoder.container(keyedBy: CodingKeys.self)
        latitude = try values.decode(Double.self, forKey: .latitude)
        longitude = try values.decode(Double.self, forKey: .longitude)
        
        let additionalInfo = try values.nestedContainer(keyedBy: AdditionalInfoKeys.self, forKey: .additionalInfo)
        elevation = try additionalInfo.decode(Double.self, forKey: .elevation)
    }
}
```



