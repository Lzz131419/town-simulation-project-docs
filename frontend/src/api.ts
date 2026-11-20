export class ApiError extends Error {
  constructor(
    message: string,
    public status = 0,
    public code = "request",
  ) {
    super(message);
  }
}
export interface RequestOptions {
  timeoutMs?: number;
  signal?: AbortSignal;
}
export async function api<T = any>(
  path: string,
  method = "GET",
  body?: unknown,
  options: RequestOptions = {},
): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(
    () => controller.abort("timeout"),
    options.timeoutMs ?? 12000,
  );
  const abort = () => controller.abort("cancelled");
  if (options.signal?.aborted) abort();
  options.signal?.addEventListener("abort", abort, { once: true });
  try {
    const r = await fetch("/api" + path, {
      method,
      credentials: "same-origin",
      signal: controller.signal,
      headers: body === undefined ? {} : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    let data: any;
    try {
      data = await r.json();
    } catch {
      if (controller.signal.aborted) throw new Error("aborted");
      throw new ApiError(
        "服务器返回了无法读取的数据，请稍后重试",
        r.status,
        "format",
      );
    }
    if (!r.ok)
      throw new ApiError(
        typeof data.detail === "string" ? data.detail : "输入内容不符合要求",
        r.status,
      );
    return data as T;
  } catch (error) {
    if (controller.signal.aborted)
      throw new ApiError(
        controller.signal.reason === "timeout"
          ? method === "GET"
            ? "连接超时，请重试"
            : "请求超时，请先刷新确认结果后再操作"
          : "请求已取消",
        0,
        controller.signal.reason === "timeout" ? "timeout" : "cancelled",
      );
    if (error instanceof ApiError) throw error;
    throw new ApiError("暂时无法连接服务器，请检查网络后重试", 0, "network");
  } finally {
    clearTimeout(timer);
    options.signal?.removeEventListener("abort", abort);
  }
}
