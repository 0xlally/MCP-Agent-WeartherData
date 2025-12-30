"""
FastAPI 主应用入口
整合所有路由和中间件
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.db.database import init_db
from app.routers import auth, admin, weather, agent, mcp, mcp_data_agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    启动时初始化数据库，关闭时清理资源
    """
    # 启动时执行
    print("🚀 正在初始化数据库...")
    await init_db()
    print("✅ 数据库初始化完成")
    
    yield
    
    # 关闭时执行
    print("👋 应用正在关闭...")


# 创建 FastAPI 应用实例
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="天气大数据服务平台 - 核心 API 网关",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# 统一维护允许跨域的来源，确保 Vite 本地调试端口可访问
allowed_origins = set(settings.CORS_ORIGINS or [])
allowed_origins.add("http://localhost:5173")


# ========== CORS 中间件配置 ==========
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(allowed_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== 注册路由 ==========
app.include_router(auth.router)      # 用户认证
app.include_router(admin.router)     # 管理员功能
app.include_router(weather.router)   # 天气数据查询 (API Key 认证)
app.include_router(agent.router)     # AI Agent 配置调整
app.include_router(mcp.router)       # MCP 工具列表
app.include_router(mcp_data_agent.router)  # MCP 数据 Agent HTTP 包装


# ========== 根路由 ==========
@app.get("/", tags=["系统"])
async def root():
    """
    API 根路径
    返回服务状态和文档链接
    """
    return {
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "运行中",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "auth": "/auth (用户注册/登录)",
            "admin": "/admin (管理员功能)",
            "weather": "/weather (天气数据查询，需 API Key)",
            "agent": "/agent (AI Agent 配置管理)"
        }
    }


@app.get("/health", tags=["系统"])
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "version": settings.VERSION
    }


# ========== 启动说明 ==========
if __name__ == "__main__":
    import uvicorn
    
    print(f"""
    ╔══════════════════════════════════════════════════╗
    ║  🌤️  天气大数据服务平台 API                      ║
    ║  Version: {settings.VERSION}                          ║
    ╚══════════════════════════════════════════════════╝
    
    📖 API 文档: http://localhost:8000/docs
    🔧 启动命令: uvicorn app.main:app --reload
    """)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
