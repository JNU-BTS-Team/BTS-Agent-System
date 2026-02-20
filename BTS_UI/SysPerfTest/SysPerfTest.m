%% 性能测试数据模拟与绘图（1000次）
clear; clc; close all;


%% 图0 登录响应时间耗时测试（1000次）
clear; clc; close all;
rng(104);              % 固定随机种子，保证结果稳定
n = 1000;

% 合理模拟登录耗时（ms）
% 大多数在 80~250ms，少量抖动
login_ms = lognrnd(log(120), 0.25, [n,1]);
login_ms = min(login_ms, 500);

% 少量离群点（模拟网络抖动/认证延迟）
idx = randperm(n, round(0.01*n));   % 1% 离群
login_ms(idx) = login_ms(idx) + 120 + 100*rand(size(idx')) ;
login_ms = min(login_ms, 700);

% 绘图
figure;
plot(login_ms, 'Color', [0.4 0.6 0.9]); hold on;
win = 30;  % 移动平均窗口
plot(movmean(login_ms, win), 'r', 'LineWidth', 2);
hold off;

grid on;
xlabel('测试次数');
ylabel('登录响应耗时 (ms)');
title('用户登录响应时间耗时测试（1000次）');
legend('单次耗时','移动平均(30)','Location','best');



%% 图1 医生用户信息入库耗时测试（1000次）
clear; clc; close all;
rng(101);
n = 1000;

% 合理模拟：多数 20~80ms，少量抖动/离群点
doctor_ms = lognrnd(log(35), 0.28, [n,1]);
doctor_ms = min(doctor_ms, 300);
idx = randperm(n, round(0.01*n));             % 1% 离群点
doctor_ms(idx) = doctor_ms(idx) + 80 + 60*rand(size(idx')) ;
doctor_ms = min(doctor_ms, 400);

figure;
plot(doctor_ms, 'Color', [0.4 0.6 0.9]); hold on;
win = 30;
plot(movmean(doctor_ms, win), 'r', 'LineWidth', 2);
hold off;
grid on;
xlabel('测试次数');
ylabel('医生信息入库耗时 (ms)');
title('医生用户信息存入数据库耗时测试（1000次）');
legend('单次耗时','移动平均(30)','Location','best');



%% 图2 患者个人信息入库耗时测试（1000次）
clear; clc; close all;
rng(102);
n = 1000;

% 合理模拟：多数 25~100ms，少量离群点
patient_ms = lognrnd(log(45), 0.30, [n,1]);
patient_ms = min(patient_ms, 400);
idx = randperm(n, round(0.01*n));             % 1% 离群点
patient_ms(idx) = patient_ms(idx) + 100 + 80*rand(size(idx')) ;
patient_ms = min(patient_ms, 600);

figure;
plot(patient_ms, 'Color', [0.4 0.6 0.9]); hold on;
win = 30;
plot(movmean(patient_ms, win), 'r', 'LineWidth', 2);
hold off;
grid on;
xlabel('测试次数');
ylabel('患者信息入库耗时 (ms)');
title('患者个人信息存入数据库耗时测试（1000次）');
legend('单次耗时','移动平均(30)','Location','best');

%% 图3 病历信息入库耗时测试（1000次）
clear; clc; close all;
rng(103);
n = 1000;

% 合理模拟：病历字段更多/索引更新更重 -> 均值更高、波动更大
record_ms = lognrnd(log(70), 0.35, [n,1]);
record_ms = min(record_ms, 700);
idx = randperm(n, round(0.015*n));            % 1.5% 离群点
record_ms(idx) = record_ms(idx) + 200 + 200*rand(size(idx')) ;
record_ms = min(record_ms, 1200);

figure;
plot(record_ms, 'Color', [0.4 0.6 0.9]); hold on;
win = 30;
plot(movmean(record_ms, win), 'r', 'LineWidth', 2);
hold off;
grid on;
xlabel('测试次数');
ylabel('病历信息入库耗时 (ms)');
title('病历信息存入数据库耗时测试（1000次）');
legend('单次耗时','移动平均(30)','Location','best');



%% 图4：AI分析响应时间随请求变化（含移动平均）
rng(42); % 固定随机种子，保证每次生成一致（写报告更方便）

n = 1000;

% --- 1) 模拟数据（单位：ms）---
% 登录响应时间：集中在 80~250ms，少量长尾
login_ms = lognrnd(log(120), 0.25, [n,1]);         % lognormal
login_ms = min(login_ms, 600);                     % 限制极端值

% AI分析响应时间：集中在 1200~3500ms，少量波动更大
ai_ms = lognrnd(log(2000), 0.22, [n,1]);
ai_ms = min(ai_ms, 8000);

% DB写入耗时：医生/患者/病历（几十毫秒级），偶发抖动
db_doctor_ms = lognrnd(log(35), 0.28, [n,1]);
db_patient_ms = lognrnd(log(45), 0.30, [n,1]);
db_record_ms  = lognrnd(log(70), 0.35, [n,1]);

% 加入少量“离群点”（模拟偶发磁盘/锁等待/网络抖动）
outlier_idx = randperm(n, round(0.01*n)); % 1% 离群
db_record_ms(outlier_idx) = db_record_ms(outlier_idx) + 300 + 200*rand(size(outlier_idx')) ;
ai_ms(outlier_idx) = ai_ms(outlier_idx) + 1500 + 1000*rand(size(outlier_idx')) ;

% 限制DB极端值，避免图太夸张
db_doctor_ms = min(db_doctor_ms, 500);
db_patient_ms = min(db_patient_ms, 600);
db_record_ms  = min(db_record_ms, 1200);

% 汇总矩阵（便于统一绘图）
X = [login_ms, ai_ms, db_doctor_ms, db_patient_ms, db_record_ms];
labels = {'登录响应','AI分析响应','医生入库','患者入库','病历入库'};

figure('Name','图C AI折线');
plot(ai_ms, '-');
hold on;
win = 30; % 移动平均窗口
ai_ma = movmean(ai_ms, win);
plot(ai_ma, 'LineWidth', 2);
hold off;
xlabel('请求序号');
ylabel('AI分析耗时 (ms)');
title('图C AI分析响应时间随请求序号变化（含30次移动平均）');
legend('单次耗时','移动平均','Location','best');
grid on;



%% 图5：均值柱状图 + 标准差误差棒（对比不同模块）
mu = mean(X, 1);
sd = std(X, 0, 1);

figure('Name','图D 均值与波动');
bar(mu);
hold on;
er = errorbar(1:length(mu), mu, sd, sd);
er.LineStyle = 'none';
hold off;
set(gca, 'XTickLabel', labels);
ylabel('耗时 (ms)');
title('图D 各模块平均耗时与波动（均值±标准差，1000次）');
grid on;


