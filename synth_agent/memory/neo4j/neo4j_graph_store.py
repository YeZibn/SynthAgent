import json
from neo4j import GraphDatabase
from typing import List, Dict, Optional
import time


class Entity:
    """知识实体"""
    
    def __init__(
        self,
        entity_id: str,
        name: str,
        type: str,
        properties: Optional[Dict] = None
    ):
        self.entity_id = entity_id
        self.name = name
        self.type = type
        self.properties = properties or {}


class Relation:
    """实体关系"""
    
    def __init__(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        properties: Optional[Dict] = None
    ):
        self.source_id = source_id
        self.target_id = target_id
        self.relation_type = relation_type
        self.properties = properties or {}


class Neo4jGraphStore:
    """Neo4j图数据库存储
    
    特点：
    - 支持连接重试机制
    - 优雅处理服务不可用情况
    - 实体和关系的CRUD操作
    - 图遍历和路径查询
    """
    
    def __init__(self, uri: str = "bolt://localhost:7687", user: str = "neo4j", password: str = "password"):
        self.uri = uri
        self.user = user
        self.password = password
        self._driver = None
        self._connected = False
        self._max_retries = 3
        self._retry_delay = 1.0
        self._init_driver()
    
    def _init_driver(self):
        """初始化Neo4j驱动"""
        try:
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_lifetime=3600,
                max_connection_pool_size=50,
                connection_timeout=10.0
            )
            
            # 测试连接
            with self._driver.session() as session:
                session.run("RETURN 1")
            
            self._connected = True
            print("Neo4j连接成功")
            
        except Exception as e:
            print(f"Neo4j连接失败: {e}")
            self._connected = False
    
    def _retry_operation(self, operation, *args, **kwargs):
        """带重试的操作"""
        for attempt in range(self._max_retries):
            try:
                if not self._connected:
                    self._init_driver()
                
                if not self._connected:
                    raise Exception("Neo4j服务不可用")
                
                return operation(*args, **kwargs)
            except Exception as e:
                if attempt < self._max_retries - 1:
                    print(f"操作失败，{self._retry_delay}秒后重试... ({attempt + 1}/{self._max_retries})")
                    time.sleep(self._retry_delay)
                    self._connected = False
                else:
                    raise e
    
    def _serialize_properties(self, properties: Dict) -> str:
        """将属性字典序列化为JSON字符串"""
        return json.dumps(properties, ensure_ascii=False)
    
    def _deserialize_properties(self, properties_str: str) -> Dict:
        """将JSON字符串反序列化为属性字典"""
        if not properties_str:
            return {}
        try:
            return json.loads(properties_str)
        except:
            return {}
    
    def close(self):
        """关闭连接"""
        if self._driver:
            self._driver.close()
            self._connected = False
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self._connected
    
    def reconnect(self):
        """重新连接"""
        self._init_driver()
    
    def add_entity(self, entity: Entity, memory_id: str, user_id: str = None, content: str = None):
        """添加实体"""
        try:
            props_json = self._serialize_properties(entity.properties)
            
            def _add_entity_tx(tx):
                tx.run(
                    """
                    MERGE (e:Entity {id: $entity_id})
                    SET e.name = $name, e.type = $type, e.props = $props, e.user_id = $user_id
                    MERGE (m:Memory {id: $memory_id})
                    SET m.user_id = $user_id, m.content = $content
                    MERGE (m)-[:CONTAINS]->(e)
                    """,
                    entity_id=entity.entity_id,
                    name=entity.name,
                    type=entity.type,
                    props=props_json,
                    memory_id=memory_id,
                    user_id=user_id,
                    content=content
                )
            
            with self._driver.session() as session:
                session.execute_write(_add_entity_tx)
            print(f"添加实体成功: {entity.name} ({entity.type})")
        except Exception as e:
            print(f"添加实体到图数据库失败: {e}")
    
    def add_relation(self, relation: Relation, memory_id: str, user_id: str = None):
        """添加关系"""
        try:
            props_json = self._serialize_properties(relation.properties)
            
            def _add_relation_tx(tx):
                query = f"""
                MERGE (s:Entity {{id: $source_id}})
                MERGE (t:Entity {{id: $target_id}})
                MERGE (s)-[r:{relation.relation_type}]->(t)
                SET r.props = $props, r.user_id = $user_id
                MERGE (m:Memory {{id: $memory_id}})
                MERGE (m)-[:CONTAINS]->(s)
                MERGE (m)-[:CONTAINS]->(t)
                """
                tx.run(
                    query,
                    source_id=relation.source_id,
                    target_id=relation.target_id,
                    props=props_json,
                    memory_id=memory_id,
                    user_id=user_id
                )
            
            with self._driver.session() as session:
                session.execute_write(_add_relation_tx)
            print(f"添加关系成功: {relation.source_id} -[{relation.relation_type}]-> {relation.target_id}")
        except Exception as e:
            print(f"添加关系到图数据库失败: {e}")
    
    def search_entities(self, search_text: str, limit: int = 10, user_id: str = None) -> List[Dict]:
        """搜索实体"""
        try:
            def _search_entities_tx(tx):
                if user_id:
                    result = tx.run(
                        """
                        MATCH (e:Entity)
                        WHERE (e.name CONTAINS $search_text OR e.type CONTAINS $search_text)
                        AND e.user_id = $user_id
                        RETURN e.id as entity_id, e.name as name, e.type as type, e.props as props, e.user_id as user_id
                        LIMIT $limit
                        """,
                        search_text=search_text,
                        limit=limit,
                        user_id=user_id
                    )
                else:
                    result = tx.run(
                        """
                        MATCH (e:Entity)
                        WHERE e.name CONTAINS $search_text OR e.type CONTAINS $search_text
                        RETURN e.id as entity_id, e.name as name, e.type as type, e.props as props, e.user_id as user_id
                        LIMIT $limit
                        """,
                        search_text=search_text,
                        limit=limit
                    )
                records = [record.data() for record in result]
                for rec in records:
                    rec['properties'] = self._deserialize_properties(rec.get('props', '{}'))
                    del rec['props']
                return records
            
            with self._driver.session() as session:
                return session.execute_read(_search_entities_tx)
        except Exception as e:
            print(f"搜索实体失败: {e}")
            return []
    
    def search_relations(self, search_text: str, limit: int = 10, user_id: str = None) -> List[Dict]:
        """搜索关系"""
        try:
            def _search_relations_tx(tx):
                if user_id:
                    result = tx.run(
                        """
                        MATCH (s:Entity)-[r]->(t:Entity)
                        WHERE (type(r) CONTAINS $search_text OR s.name CONTAINS $search_text OR t.name CONTAINS $search_text)
                        AND r.user_id = $user_id
                        RETURN s.id as source_id, s.name as source_name, 
                               t.id as target_id, t.name as target_name, 
                               type(r) as relation_type, r.props as props, r.user_id as user_id
                        LIMIT $limit
                        """,
                        search_text=search_text,
                        limit=limit,
                        user_id=user_id
                    )
                else:
                    result = tx.run(
                        """
                        MATCH (s:Entity)-[r]->(t:Entity)
                        WHERE type(r) CONTAINS $search_text OR s.name CONTAINS $search_text OR t.name CONTAINS $search_text
                        RETURN s.id as source_id, s.name as source_name, 
                               t.id as target_id, t.name as target_name, 
                               type(r) as relation_type, r.props as props, r.user_id as user_id
                        LIMIT $limit
                        """,
                        search_text=search_text,
                        limit=limit
                    )
                records = [record.data() for record in result]
                for rec in records:
                    rec['properties'] = self._deserialize_properties(rec.get('props', '{}'))
                    del rec['props']
                return records
            
            with self._driver.session() as session:
                return session.execute_read(_search_relations_tx)
        except Exception as e:
            print(f"搜索关系失败: {e}")
            return []
    
    def get_entity_by_id(self, entity_id: str) -> Optional[Dict]:
        """根据ID获取实体"""
        try:
            def _get_entity_tx(tx):
                result = tx.run(
                    """
                    MATCH (e:Entity {id: $entity_id})
                    RETURN e.id as entity_id, e.name as name, e.type as type, e.props as props
                    """,
                    entity_id=entity_id
                )
                record = result.single()
                if record:
                    data = record.data()
                    data['properties'] = self._deserialize_properties(data.get('props', '{}'))
                    del data['props']
                    return data
                return None
            
            with self._driver.session() as session:
                return session.execute_read(_get_entity_tx)
        except Exception as e:
            print(f"获取实体失败: {e}")
            return None
    
    def get_entity_relations(self, entity_id: str, limit: int = 10) -> List[Dict]:
        """获取实体的所有关系"""
        try:
            def _get_relations_tx(tx):
                result = tx.run(
                    """
                    MATCH (e:Entity {id: $entity_id})-[r]-(other:Entity)
                    RETURN e.id as entity_id, e.name as entity_name,
                           other.id as related_id, other.name as related_name,
                           type(r) as relation_type, r.props as props,
                           CASE WHEN startNode(r) = e THEN 'outgoing' ELSE 'incoming' END as direction
                    LIMIT $limit
                    """,
                    entity_id=entity_id,
                    limit=limit
                )
                records = [record.data() for record in result]
                for rec in records:
                    rec['properties'] = self._deserialize_properties(rec.get('props', '{}'))
                    del rec['props']
                return records
            
            with self._driver.session() as session:
                return session.execute_read(_get_relations_tx)
        except Exception as e:
            print(f"获取实体关系失败: {e}")
            return []
    
    def find_path(self, start_entity_id: str, end_entity_id: str, max_depth: int = 3) -> List[Dict]:
        """查找两个实体之间的路径"""
        try:
            def _find_path_tx(tx):
                query = f"""
                MATCH path = shortestPath(
                    (start:Entity {{id: $start_id}})-[*1..{max_depth}]-(end:Entity {{id: $end_id}})
                )
                RETURN [node in nodes(path) | {{id: node.id, name: node.name, type: node.type}}] as nodes,
                       [rel in relationships(path) | {{type: type(rel), properties: rel.props}}] as relations
                """
                result = tx.run(
                    query,
                    start_id=start_entity_id,
                    end_id=end_entity_id
                )
                return [record.data() for record in result]
            
            with self._driver.session() as session:
                return session.execute_read(_find_path_tx)
        except Exception as e:
            print(f"查找路径失败: {e}")
            return []
    
    def delete_entity(self, entity_id: str):
        """删除实体及其关系"""
        try:
            def _delete_entity_tx(tx):
                tx.run(
                    """
                    MATCH (e:Entity {id: $entity_id})
                    DETACH DELETE e
                    """,
                    entity_id=entity_id
                )
            
            with self._driver.session() as session:
                session.execute_write(_delete_entity_tx)
            print(f"删除实体成功: {entity_id}")
        except Exception as e:
            print(f"删除实体失败: {e}")
    
    def delete_relation(self, source_id: str, target_id: str, relation_type: str):
        """删除关系"""
        try:
            def _delete_relation_tx(tx):
                query = f"""
                MATCH (s:Entity {{id: $source_id}})-[r:{relation_type}]->(t:Entity {{id: $target_id}})
                DELETE r
                """
                tx.run(
                    query,
                    source_id=source_id,
                    target_id=target_id
                )
            
            with self._driver.session() as session:
                session.execute_write(_delete_relation_tx)
            print(f"删除关系成功: {source_id} -[{relation_type}]-> {target_id}")
        except Exception as e:
            print(f"删除关系失败: {e}")
    
    def get_memory_contents(self, memory_id: str) -> Dict:
        """获取记忆包含的所有实体和关系"""
        try:
            def _get_memory_contents_tx(tx):
                result = tx.run(
                    """
                    MATCH (m:Memory {id: $memory_id})-[:CONTAINS]->(e:Entity)
                    OPTIONAL MATCH (e)-[r]->(other:Entity)
                    WHERE (m)-[:CONTAINS]->(other)
                    RETURN collect(DISTINCT {
                        entity_id: e.id,
                        name: e.name,
                        type: e.type,
                        properties: e.props
                    }) as entities,
                    collect(DISTINCT {
                        source_id: e.id,
                        source_name: e.name,
                        target_id: other.id,
                        target_name: other.name,
                        relation_type: type(r),
                        properties: r.props
                    }) as relations
                    """,
                    memory_id=memory_id
                )
                record = result.single()
                if record:
                    entities = []
                    for e in record["entities"]:
                        if e["entity_id"]:
                            entities.append({
                                "entity_id": e["entity_id"],
                                "name": e["name"],
                                "type": e["type"],
                                "properties": self._deserialize_properties(e.get("properties", "{}"))
                            })
                    
                    relations = []
                    for r in record["relations"]:
                        if r["source_id"] and r["target_id"]:
                            relations.append({
                                "source_id": r["source_id"],
                                "source_name": r["source_name"],
                                "target_id": r["target_id"],
                                "target_name": r["target_name"],
                                "relation_type": r["relation_type"],
                                "properties": self._deserialize_properties(r.get("properties", "{}"))
                            })
                    
                    return {
                        "memory_id": memory_id,
                        "entities": entities,
                        "relations": relations,
                        "entity_count": len(entities),
                        "relation_count": len(relations)
                    }
                return None
            
            with self._driver.session() as session:
                return session.execute_read(_get_memory_contents_tx)
        except Exception as e:
            print(f"获取记忆内容失败: {e}")
            return None
    
    def get_stats(self, user_id: Optional[str] = None) -> Dict:
        """获取图统计信息"""
        try:
            def _get_stats_tx(tx):
                if user_id:
                    entity_count = tx.run("MATCH (e:Entity {user_id: $user_id}) RETURN count(e) as count", user_id=user_id).single()["count"]
                    relation_count = tx.run("MATCH (:Entity {user_id: $user_id})-[r]->(:Entity {user_id: $user_id}) RETURN count(r) as count", user_id=user_id).single()["count"]
                    memory_count = tx.run("MATCH (m:Memory {user_id: $user_id}) RETURN count(m) as count", user_id=user_id).single()["count"]
                else:
                    entity_count = tx.run("MATCH (e:Entity) RETURN count(e) as count").single()["count"]
                    relation_count = tx.run("MATCH ()-[r]->() RETURN count(r) as count").single()["count"]
                    memory_count = tx.run("MATCH (m:Memory) RETURN count(m) as count").single()["count"]
                return {
                    "entity_count": entity_count,
                    "relation_count": relation_count,
                    "memory_count": memory_count
                }
            
            with self._driver.session() as session:
                return session.execute_read(_get_stats_tx)
        except Exception as e:
            print(f"获取统计信息失败: {e}")
            return {"entity_count": 0, "relation_count": 0, "memory_count": 0}
    
    def clear_all(self):
        """清空所有数据（慎用）"""
        try:
            def _clear_all_tx(tx):
                tx.run("MATCH (n) DETACH DELETE n")
            
            with self._driver.session() as session:
                session.execute_write(_clear_all_tx)
            print("已清空所有图数据")
        except Exception as e:
            print(f"清空数据失败: {e}")


if __name__ == "__main__":
    import os
    
    # 从环境变量获取配置
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "12345678")
    
    # 初始化图存储
    graph_store = Neo4jGraphStore(
        uri=neo4j_uri,
        user=neo4j_user,
        password=neo4j_password
    )
    
    # 检查连接状态
    print(f"连接状态: {graph_store.is_connected()}")
    
    if graph_store.is_connected():
        # 测试添加实体
        print("\n--- 测试添加实体 ---")
        entity1 = Entity(
            entity_id="person_001",
            name="张三",
            type="PERSON",
            properties={"age": 25, "city": "北京"}
        )
        entity2 = Entity(
            entity_id="org_001",
            name="清华大学",
            type="ORG",
            properties={"location": "北京"}
        )
        
        graph_store.add_entity(entity1, "memory_001")
        graph_store.add_entity(entity2, "memory_001")
        
        # 测试添加关系
        print("\n--- 测试添加关系 ---")
        relation = Relation(
            source_id="person_001",
            target_id="org_001",
            relation_type="就读于",
            properties={"since": "2020"}
        )
        graph_store.add_relation(relation, "memory_001")
        
        # 测试搜索实体
        print("\n--- 测试搜索实体 ---")
        entities = graph_store.search_entities("张三")
        for entity in entities:
            print(f"  找到实体: {entity['name']} ({entity['type']}) 属性: {entity['properties']}")
        
        # 测试搜索关系
        print("\n--- 测试搜索关系 ---")
        relations = graph_store.search_relations("就读于")
        for rel in relations:
            print(f"  找到关系: {rel['source_name']} -[{rel['relation_type']}]-> {rel['target_name']}")
        
        # 测试获取实体关系
        print("\n--- 测试获取实体关系 ---")
        entity_relations = graph_store.get_entity_relations("person_001")
        for rel in entity_relations:
            print(f"  {rel['entity_name']} -[{rel['relation_type']}]-> {rel['related_name']} ({rel['direction']})")
        
        # 测试统计信息
        print("\n--- 图统计信息 ---")
        stats = graph_store.get_stats()
        print(f"  实体数量: {stats['entity_count']}")
        print(f"  关系数量: {stats['relation_count']}")
        print(f"  记忆数量: {stats['memory_count']}")
        
        # 测试查找路径
        print("\n--- 测试查找路径 ---")
        # 先添加另一个实体和关系
        entity3 = Entity(
            entity_id="city_001",
            name="北京",
            type="LOCATION",
            properties={"population": "2100万"}
        )
        graph_store.add_entity(entity3, "memory_001")
        
        relation2 = Relation(
            source_id="org_001",
            target_id="city_001",
            relation_type="位于",
            properties={}
        )
        graph_store.add_relation(relation2, "memory_001")
        
        # 查找路径
        paths = graph_store.find_path("person_001", "city_001", max_depth=3)
        for path in paths:
            print(f"  路径: {' -> '.join([n['name'] for n in path['nodes']])}")
        
        # 清理测试数据
        print("\n--- 清理测试数据 ---")
        graph_store.clear_all()
        
    # 关闭连接
    graph_store.close()
    print("\n测试完成!")
