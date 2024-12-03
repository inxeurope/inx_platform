CREATE PROCEDURE __zotta
AS
DECLARE @RC int
EXECUTE @RC = [dbo].[_drop_all_views_and_sprocs]
EXECUTE @RC = [dbo].[_drop_all_tables]