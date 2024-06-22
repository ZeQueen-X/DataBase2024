DROP TRIGGER IF EXISTS trg_applyInsert;
DROP TRIGGER IF EXISTS trg_applyUpdate;
DROP TRIGGER IF EXISTS trg_dormDeleted;
DELIMITER $$

# 新添申请时设置触发器自动更改状态
CREATE TRIGGER trg_applyInsert
    AFTER INSERT ON management_dormapply
    FOR EACH ROW
    BEGIN
        DECLARE stu_status INT;
        SELECT management_student.status INTO stu_status
        FROM management_student
            WHERE student_id = NEW.applicant_id;

        IF stu_status = 0 THEN
            UPDATE management_student
                SET status = 1
            WHERE student_id = NEW.applicant_id;
        end if;
        IF stu_status = 2 THEN
            UPDATE management_student
                SET status = 3
            WHERE student_id = NEW.applicant_id;
        end if;
    end $$

CREATE TRIGGER trg_applyUpdate
    AFTER UPDATE ON management_dormapply
    FOR EACH ROW
    BEGIN
        DECLARE stu_status INT;
        SELECT management_student.status INTO stu_status
        FROM management_student
            WHERE student_id = NEW.applicant_id;
        # 表示同意入住或拒绝退宿，将状态更改成已入宿
        IF (stu_status = 1 AND NEW.status = 1) OR (stu_status=3 AND NEW.status = 2) THEN
            UPDATE management_student
                SET status = 2
            WHERE student_id = NEW.applicant_id;
        end if;
         # 表示拒绝入住或同意退宿，将状态更改成未入宿
        IF (stu_status = 3 AND NEW.status =1) OR (stu_status = 1 AND NEW.status = 2)  THEN
            UPDATE management_student
                SET status = 0,dorm_id = NULL
            WHERE student_id = NEW.applicant_id;
        end if;
    end $$

CREATE  TRIGGER  trg_dormDeleted
    before UPDATE ON management_student
    FOR EACH ROW
    BEGIN
        -- 如果由有宿舍变成无宿舍，且不是申请造成的
        IF NEW.dorm_id IS NULL AND OLD.dorm_id IS NOT NULL  AND EXISTS(SELECT * FROM management_dormapply WHERE applicant_id = NEW.student_id AND apply_type = 1 AND status = 0) THEN
            -- 将未处理的退宿申请改为同意
            SET NEW.status = 0;
            DELETE  FROM management_dormapply
                 WHERE applicant_id = NEW.student_id AND apply_type = 1 AND status = 0;
        end if;
    end $$

DELIMITER ;