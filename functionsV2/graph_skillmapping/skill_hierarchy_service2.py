from database import db

class SkillHierarchyCompleteService:
    
    def get_complete_hierarchy_optimized(self):
        """
        Get complete skill hierarchy without limit - optimized version
        Uses a single query with aggregation to reduce memory footprint
        """
        try:
            with db.get_cursor() as cursor:
                # Optimized query that groups frameworks under skills
                query = """
                    WITH framework_agg AS (
                        SELECT 
                            shl.domain_id,
                            shl.discipline_id,
                            shl.skill_id,
                            json_agg(
                                json_build_object(
                                    'id', shl.framework_id,
                                    'name', mf.framework_name,
                                    'label', 'Framework'
                                ) ORDER BY mf.framework_name
                            ) as frameworks
                        FROM "SkillHierarchyLink" shl
                        LEFT JOIN "MasterFramework" mf ON shl.framework_id = mf.id
                        GROUP BY shl.domain_id, shl.discipline_id, shl.skill_id
                    ),
                    skill_agg AS (
                        SELECT 
                            fa.domain_id,
                            fa.discipline_id,
                            json_agg(
                                json_build_object(
                                    'id', fa.skill_id,
                                    'name', ms.skill_name,
                                    'label', 'Skill',
                                    'children', fa.frameworks
                                ) ORDER BY ms.skill_name
                            ) as skills
                        FROM framework_agg fa
                        LEFT JOIN "MasterSkill" ms ON fa.skill_id = ms.id
                        GROUP BY fa.domain_id, fa.discipline_id
                    ),
                    discipline_agg AS (
                        SELECT 
                            sa.domain_id,
                            json_agg(
                                json_build_object(
                                    'id', sa.discipline_id,
                                    'name', mdisc.discipline_name,
                                    'label', 'Discipline',
                                    'children', sa.skills
                                ) ORDER BY mdisc.discipline_name
                            ) as disciplines
                        FROM skill_agg sa
                        LEFT JOIN "MasterDiscipline" mdisc ON sa.discipline_id = mdisc.id
                        GROUP BY sa.domain_id
                    )
                    SELECT 
                        json_agg(
                            json_build_object(
                                'id', da.domain_id,
                                'name', md.domain_name,
                                'label', 'Domain',
                                'children', da.disciplines
                            ) ORDER BY md.domain_name
                        ) as hierarchy
                    FROM discipline_agg da
                    LEFT JOIN "MasterDomain" md ON da.domain_id = md.id
                """
                
                cursor.execute(query)
                result = cursor.fetchone()
                
                if result and result['hierarchy']:
                    data = result['hierarchy']
                    
                    # Calculate counts
                    total_domains = len(data)
                    total_disciplines = sum(len(domain.get('children', [])) for domain in data)
                    total_skills = sum(
                        len(discipline.get('children', [])) 
                        for domain in data 
                        for discipline in domain.get('children', [])
                    )
                    total_frameworks = sum(
                        len(skill.get('children', [])) 
                        for domain in data 
                        for discipline in domain.get('children', [])
                        for skill in discipline.get('children', [])
                    )
                    
                    return {
                        "status": "success",
                        "total_domains": total_domains,
                        "total_disciplines": total_disciplines,
                        "total_skills": total_skills,
                        "total_frameworks": total_frameworks,
                        "data": data
                    }
                else:
                    return {
                        "status": "success",
                        "total_domains": 0,
                        "total_disciplines": 0,
                        "total_skills": 0,
                        "total_frameworks": 0,
                        "data": []
                    }
                
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

skill_hierarchy_complete_service = SkillHierarchyCompleteService()