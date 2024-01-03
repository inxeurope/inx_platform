change email address of users zz_* because otherwise there will be a duplication
UPDATE Users
SET email = 'zz_non-emea@inxeurope.com'
WHERE ID_SalesManager = 6

UPDATE Users
SET email = 'zz_admin@inxeurope.com'
WHERE ID_SalesManager = 8

The user marco.zanella@inxeurop.com must also be changed before importing because it would create a duplicate

Nel database SQL in _BudForDetails, nei dati di Emanuele ci sono 25 linee con volume e prezzo nullo, di cui 23 di durst e 1 di aeoon - sistemare in SQL app e zippare i dati

Learn date (created_at)
Learn created_by

loader
