import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function Page() {
  return (
    <div className="@container/main flex flex-col gap-4 md:gap-6">
      <Card>
        <CardHeader>
          <CardTitle>T-EEG Dashboard</CardTitle>
          <CardDescription>业务页面待接入。</CardDescription>
        </CardHeader>
        <CardContent className="text-muted-foreground text-sm">
          模板 Demo 页面已清空。请参考 <code>DEVELOPMENT.md</code> 在此目录或新建路由下接入 EEG 业务页面与后端 API。
        </CardContent>
      </Card>
    </div>
  );
}
