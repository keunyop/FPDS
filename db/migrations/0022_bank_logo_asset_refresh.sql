BEGIN;

-- Keep an operator-supplied custom logo URL intact. This refresh replaces only
-- the favicon defaults introduced with the recognized-bank seed.
WITH official_logo_refresh(bank_code, previous_logo_url, logo_url, logo_alt_text) AS (
    VALUES
        ('RBC', 'https://www.rbcroyalbank.com/favicon.ico', 'https://www.rbcroyalbank.com/dvl/assets/images/logos/rbc-logo-shield.svg', 'Royal Bank of Canada logo'),
        ('TD', 'https://www.td.com/favicon.ico', 'https://www.td.com/content/dam/tdct/images/navigation-header-and-footer/td-logo-mobile.png', 'TD Bank logo'),
        ('SCOTIA', 'https://www.scotiabank.com/favicon.ico', 'https://www.scotiabank.com/content/dam/scotiabank/images/logos/2019/scotiabank-logo-red-desktop-200px.svg', 'Scotiabank logo'),
        ('CIBC', 'https://www.cibc.com/favicon.ico', 'https://www.cibc.com/content/dam/global-assets/logos/cibc-logos/no-tagline/cibc-logo-colour-142x36.svg', 'CIBC logo'),
        ('NATIONAL', 'https://www.nbc.ca/favicon.ico', 'https://www.nbc.ca/content/dam/bnc/commun/logo/logo-nbc-155x50.svg', 'National Bank of Canada logo'),
        ('LAURENTIAN', 'https://www.laurentianbank.ca/favicon.ico', 'https://images.ctfassets.net/b5xlbty9p8dy/1N5u3c9NZEFH5cFWZjGuYO/b8ede62d4fe64efdcfcc279667cc450e/Logo.svg', 'Laurentian Bank of Canada logo'),
        ('TANGERINE', 'https://www.tangerine.ca/favicon.ico', 'https://www.tangerine.ca/content/experience-fragments/tangerine/ca/en/header/master/_jcr_content/root/container_1282085336/container_745983912/container_1531797112_822927059/image.coreimg.svg/1777585120988/logo-tangerine-orange.svg', 'Tangerine Bank logo'),
        ('EQBANK', 'https://www.eqbank.ca/favicon.ico', 'https://images.ctfassets.net/ymwa45h4u77x/4oX5L57Tc4Xrv2iKG72VPN/481fb11b7a59027ebd4316579313fe3d/eqbank-logo.svg', 'EQ Bank logo'),
        ('MANULIFE', 'https://www.manulifebank.ca/favicon.ico', 'https://www.manulifebank.ca/content/dam/manulife-bank/en_ca/logo/Manulife_Bank_ni_logo_black.svg', 'Manulife Bank of Canada logo'),
        ('ALTERNA', 'https://www.alternabank.ca/favicon.ico', 'https://www.alternabank.ca/media/vxmi4hy5/alterna-bank.svg', 'Alterna Bank logo'),
        ('BRIDGEWATER', 'https://www.bridgewaterbank.ca/favicon.ico', 'https://bridgewaterbank.ca/wp-content/uploads/2018/10/logo-black.svg', 'Bridgewater Bank logo'),
        ('CTBANK', 'https://www.ctfs.com/favicon.ico', 'https://media.ctfs.com/navigation/NAV_CTB_EN_Logo.svg', 'Canadian Tire Bank logo'),
        ('FAIRSTONE', 'https://www.fairstone.ca/favicon.ico', 'https://www.fairstone.ca/content/dam/fs/logos/FairstoneLogo_EN.svg', 'Fairstone Bank of Canada logo'),
        ('FNBC', 'https://www.fnbc.ca/favicon.ico', 'https://www.fnbc.ca/assets/img/logos/FNBC_Logo_Full.png', 'First Nations Bank of Canada logo'),
        ('OAKEN', 'https://www.oaken.com/favicon.ico', 'https://www.oaken.com/media/5lejbr01/oaken-bil-logo_rgb.png', 'Oaken Financial logo'),
        ('HAVENTREE', 'https://www.haventreebank.com/favicon.ico', 'https://images.ctfassets.net/hw93zeuesbqv/2KM8tvJXRifNUcZUOJRa4c/f69db98d25b1601edbe96c820f7fbdcd/HT_Symbol__2_.png', 'Haventree Bank logo'),
        ('RFA', 'https://www.rfa.ca/favicon.ico', 'https://www.rfa.ca/logo.svg', 'RFA Bank of Canada logo'),
        ('ROGERSBANK', 'https://www.rogersbank.com/favicon.ico', 'https://selfserve.rogersbank.com/icons/rb_logo.png', 'Rogers Bank logo'),
        ('SIMPLII', 'https://www.simplii.com/favicon.ico', 'https://www.simplii.com/content/dam/simplii-assets/global/logos/simplii-logos/horizontal/simplii-financial-logotype-full-pink.svg', 'Simplii Financial logo'),
        ('VERSABANK', 'https://www.versabank.com/favicon.ico', 'https://www.versabank.com/wp-content/uploads/2024/10/logo-versabank-en.png', 'VersaBank logo'),
        ('WEALTHONE', 'https://www.wealthonebankofcanada.com/favicon.ico', 'https://www.wealthonebankofcanada.com/img/logos/wealth-one-header-logo.svg', 'Wealth One Bank of Canada logo'),
        ('B2B', 'https://b2bbank.com/favicon.ico', 'https://b2bbank.com/sn_uploads/grid/B2B-Bank_EN_2-web_1.svg', 'B2B Bank logo')
)
UPDATE bank AS bank
SET
    logo_url = official_logo_refresh.logo_url,
    logo_alt_text = official_logo_refresh.logo_alt_text,
    updated_at = now()
FROM official_logo_refresh
WHERE bank.bank_code = official_logo_refresh.bank_code
  AND (bank.logo_url IS NULL OR bank.logo_url = official_logo_refresh.previous_logo_url);

INSERT INTO migration_history (migration_name)
VALUES ('0022_bank_logo_asset_refresh.sql')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
