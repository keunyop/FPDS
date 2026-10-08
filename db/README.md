# FPDS 신규 DB 구축

빈 PostgreSQL DB에 FPDS schema와 초기 기준 데이터를 구성하는 방법이다.
아래 명령은 저장소 루트의 PowerShell에서 실행한다.

## 1. 준비

- PostgreSQL 서버, 접속 가능한 빈 DB와 해당 DB의 schema를 생성할 계정을 준비한다.
- `psql`을 설치하고 PATH에서 실행할 수 있게 한다.
- PostgreSQL 서버에 `pgvector`를 설치한다. 전체 migration 적용 과정의
  `0012`에서 `vector` extension을 생성하므로 extension 생성 권한도 필요하다.
  권한이 제한된 환경에서는 DB 관리자가 대상 DB에 extension을 먼저 생성한다.
- [.env.dev.example](../.env.dev.example)을 참고해 로컬 `.env.dev`의
  `FPDS_DATABASE_URL`을 신규 개발 DB의 연결 정보로 설정한다. 연결 정보는 Git에 넣지 않는다.

`psql`은 `.env.dev`를 자동으로 읽지 않는다. 같은 연결 정보를 현재 터미널에도 설정한다.

```powershell
$env:FPDS_DATABASE_URL = 'postgres://fpds_dev_user:replace-me@localhost:5432/fpds_dev'
psql -X "$env:FPDS_DATABASE_URL" -v ON_ERROR_STOP=1 -c 'SELECT current_database(), current_user;'
```

예시의 계정·암호·host·port·DB 이름을 준비한 환경 값으로 바꾼다.
출력에서 신규 DB와 실행 계정을 확인한 뒤 다음 단계로 진행한다.

## 2. 전체 migration 적용

[migrations](migrations)의 SQL 파일을 이름의 번호순으로 모두 적용한다.
현재 순서는 `0001`부터 `0047`까지이며, 중간 파일도 생략하지 않는다.
SQL 파일에 정의된 transaction 범위대로 적용하며 오류가 발생하면 다음 파일로 진행하지 않는다.

```powershell
if ([string]::IsNullOrWhiteSpace($env:FPDS_DATABASE_URL)) {
    throw 'FPDS_DATABASE_URL을 신규 DB 연결 정보로 설정하세요.'
}

$fpdsMigrations = @(Get-ChildItem -LiteralPath 'db/migrations' -Filter '*.sql' -File | Sort-Object Name)
if ($fpdsMigrations.Count -eq 0) {
    throw '저장소 루트에서 실행하고 db/migrations를 확인하세요.'
}

foreach ($fpdsMigration in $fpdsMigrations) {
    Write-Host "Applying $($fpdsMigration.Name)"
    psql -X "$env:FPDS_DATABASE_URL" -v ON_ERROR_STOP=1 -f "$($fpdsMigration.FullName)"
    if ($LASTEXITCODE -ne 0) {
        throw "Migration 실패: $($fpdsMigration.Name). 원인을 해결하기 전 다음 파일을 적용하지 마세요."
    }
}
```

SQL 오류가 발생하면 실행이 멈춘다. 명시적 transaction 안에서 실패한 변경은 취소된다.
앞서 성공한 파일은 이미 반영되어 있으므로, 실패 원인과 반영 상태를 확인한 뒤
실패한 파일부터 나머지 파일을 번호순으로 적용한다.

## 3. 구축 확인

```powershell
psql -X "$env:FPDS_DATABASE_URL" -v ON_ERROR_STOP=1 -c 'SELECT migration_name FROM migration_history ORDER BY migration_name;'
psql -X "$env:FPDS_DATABASE_URL" -v ON_ERROR_STOP=1 -c 'SELECT count(*) AS applied_migrations FROM migration_history;'
psql -X "$env:FPDS_DATABASE_URL" -v ON_ERROR_STOP=1 -c '\dt'
psql -X "$env:FPDS_DATABASE_URL" -v ON_ERROR_STOP=1 -c 'SELECT country_code, status FROM country_registry ORDER BY country_code;'
```

적용 기록을 확인한다. 현재 47개 SQL 파일을 모두 적용하면
44개 기록과 마지막 `0047_product_type_collection_fields.sql`이 남는다.
`0009`, `0014`, `0015`는 적용 기록을 추가하지 않으므로 SQL 실행 결과도 함께 확인한다.
테이블과 국가 기준 데이터도 확인한다.

초기 기준 데이터는 migration에 포함되며 실제 수집 상품이나 Public 결과를
채우지는 않는다. 은행·상품 유형·출처 registry는 API를 실행하거나 조회하는
것만으로 자동으로 채워지지 않는다. 필요한 추가 등록은 Admin의 운영 기능을 사용한다.

## 4. 최초 계정과 앱 실행

[API README의 최초 운영 계정 bootstrap](../api/service/README.md#local-run)을
따라 계정을 생성한다. API가 동일한 신규 DB의 `.env.dev`를 사용하도록 설정하고,
[개발 가이드](../descent/FPDS_Admin_개발_가이드.md#2-처음-실행하기)에 따라
API와 Admin을 실행한 뒤 로그인과 국가 선택을 확인한다.
