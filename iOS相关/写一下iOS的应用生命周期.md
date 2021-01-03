[TOC]

# 写一下iOS的应用生命周期

​	现在已经是1202年了，iOS的版本都已经更新到了iOS14，相应的，其iOS的生命周期管理也在先前的版本中发生了改变，而网络上大部分文章所讲内容都已经过时。出于学习和总结的目的，开一个坑来写这个东西，如果有什么不对的地方我们再改就好了

# 什么是生命周期

​	应用在其运行/存留的时期总会经历各种各样的状态，诸如按下Home键被放入后台、被突如其来的电话打断之类的，我们把这一套从应用被运行到被终止的状态变化过程称为应用的生命周期。在iOS13之前，程序的生命周期可以被分为以下五种

+ Not Running —— 未运行，此时程序还未启动。

+ Inactive —— 不活跃，通常出现在状态转移的中间过程中，表示程序仍在前台运行，但是不能够接受任何外部的事件并进行处理，例如用户没有退出应用程序的界面就锁屏了的情况。

+ Active —— 活跃，应用正在运行并且接收事件做出反馈。

+ Background —— 后台运行， 进入后台运行有两种情况：

  1. 按下Home键或者切换到其他应用将应用推入后台
  2. 应用指定直接从Not Running启动至Background状态

  在以上这两种状况中，程序会在后台短暂的运行，经过一定时间后就会被系统在不通知的情况下挂起（Suspended），进入休眠状态。如果程序明确指定了需要在后台运行，则不会受到这一因素的影响，可以在后台常驻运行。

+ Suspended —— 挂起，此时的应用不执行任何的代码，但是保留相关的资源和上下文，直到系统内存告急被强制终止以释放更多资源或被用户手动唤醒。

# iOS13以后的状况

​	在iOS13及以后，应用的生命周期发生了变化，因为要配合iPadOS的发布以支持多窗口操作。在原本的情况中，一个应用通常有且只会有一个窗口（window），不存在多个窗口的情况，一次只能运行一个；而在iOS13中，应用可以同时打开多个窗口，其被称之为Session（会话），用以取代原本窗口的概念，一个会话中可以存在有多个Scene（场景）。生命周期管理的重心也因此转移到了场景上，我们将在这里重点讨论这个话题。

​	在iOS13之前，应用的生命周期全权由AppDelegate负责，而在iOS13及以后的版本中，应用的生命周期被割裂成两块，AppDelegate只负责整个应用的启动和终结，而SceneDelegate则接手了原本AppDelegate的大部分职责，控制一个场景的应用状态的转移。为此，iOS13中出现了一种全新的状态——Unattached，用以表示场景未被“连接”上的状态（有别于原有的Not Running，程序本体仍然存在创建和销毁的过程）。

​	我们简要概述一下在iOS13及以后的版本中，应用的生命周期的一般情况

1. 用户点击应用图标
2. 程序进入main函数，调用UIApplicationMain函数
3. 初始化UIApplication对象并且指定AppDelegate和SceneDelegate
4. 程序完成加载，调用`application(_ application: UIApplication, didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool`
5. UIKit创建并连接场景到特定会话时，调用`application(_ application: UIApplication, configurationForConnecting connectingSceneSession: UISceneSession, options: UIScene.ConnectionOptions) -> UISceneConfiguration`（选择特定的配置来创建场景）和`scene(_ scene: UIScene, willConnectTo session: UISceneSession, options connectionOptions: UIScene.ConnectionOptions)`（当场景被连接时调用）
6. 场景即将进入前台时，调用`sceneWillEnterForeground(_ scene: UIScene)`
7. 场景处于活跃状态，调用`sceneDidBecomeActive(_ scene: UIScene)`
8. 用户按下Home键时：
   1. 取消活跃状态，调用`sceneWillResignActive(_ scene: UIScene)`
   2. 场景被推入后台，调用`sceneDidEnterBackground(_ scene: UIScene)`
   3. 经过一定时间未被重新推入前台后，调用`sceneDidDisconnect(_ scene: UIScene)`，进入suspended状态
9. 用户重新进入场景时：
   1. 如果场景未处于Background状态，调用`scene(_ scene: UIScene, willConnectTo session: UISceneSession, options connectionOptions: UIScene.ConnectionOptions)`，重新连接至会话
   2. 场景被推入前台，调用`sceneWillEnterForeground(_ scene: UIScene)`
   3. 标识活跃状态，调用`sceneDidBecomeActive(_ scene: UIScene)`
10. 当用户进入后台卡片界面时，调用`sceneWillResignActive(_ scene: UIScene)`
11. 当场景被关闭时，调用`sceneDidDisconnect(_ scene: UIScene)`
12. 当会话被关闭时，调用`func sceneDidDisconnect(_ scene: UIScene)`和`application(_ application: UIApplication, didDiscardSceneSessions sceneSessions: Set<UISceneSession>)`
13. 当应用被关闭时，调用`applicationWillTerminate(_ application: UIApplication)`

