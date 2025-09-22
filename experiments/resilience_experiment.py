"""
Experimento de Resiliencia - Saga Pattern
Valida la capacidad del sistema para manejar fallos y recuperarse automáticamente
"""
import asyncio
import aiohttp
import time
import json
import random
from datetime import datetime, timezone
from typing import List, Dict, Any
import uuid

# Configuración del experimento
BFF_BASE_URL = "http://localhost:8000"
TOTAL_SCENARIOS = 20
FAILURE_INJECTION_RATE = 0.3  # 30% de requests con fallas inducidas

class ResilienceExperiment:
    def __init__(self):
        self.scenarios_results = []
        
    async def create_normal_saga(self, session: aiohttp.ClientSession, scenario_id: int) -> Dict[str, Any]:
        """Crear saga normal (sin fallas inducidas)"""
        payload = {
            "affiliate_name": f"Normal User {scenario_id}",
            "affiliate_email": f"normal.user.{scenario_id}@example.com",
            "commission_rate": 0.15,
            "content_type": "BLOG",
            "content_title": f"Normal Content {scenario_id}",
            "content_description": f"Normal content description for scenario {scenario_id}",
            "collaboration_type": "CONTENT_CREATION"
        }
        
        return await self.execute_saga_scenario(session, scenario_id, payload, "NORMAL")
    
    async def create_failing_saga(self, session: aiohttp.ClientSession, scenario_id: int) -> Dict[str, Any]:
        """Crear saga con falla inducida"""
        failure_type = random.choice(["DUPLICATE_EMAIL", "INVALID_RATE", "TIMEOUT_SIM"])
        
        if failure_type == "DUPLICATE_EMAIL":
            # Email duplicado para forzar falla
            payload = {
                "affiliate_name": f"Failing User {scenario_id}",
                "affiliate_email": "duplicate.email@example.com",  # Email fijo para duplicado
                "commission_rate": 0.15,
                "content_type": "BLOG",
                "content_title": f"Failing Content {scenario_id}",
                "content_description": f"Content that should fail due to duplicate email",
                "collaboration_type": "CONTENT_CREATION"
            }
        elif failure_type == "INVALID_RATE":
            # Tasa de comisión inválida
            payload = {
                "affiliate_name": f"Failing User {scenario_id}",
                "affiliate_email": f"failing.user.{scenario_id}@example.com",
                "commission_rate": 1.5,  # Tasa inválida > 1.0
                "content_type": "BLOG",
                "content_title": f"Failing Content {scenario_id}",
                "content_description": f"Content that should fail due to invalid commission rate",
                "collaboration_type": "CONTENT_CREATION"
            }
        else:  # TIMEOUT_SIM
            # Simular timeout con campos complejos
            payload = {
                "affiliate_name": f"Timeout User {scenario_id}",
                "affiliate_email": f"timeout.user.{scenario_id}@example.com",
                "commission_rate": 0.15,
                "content_type": "COMPLEX_VIDEO",
                "content_title": f"Complex Content {scenario_id}" * 50,  # Título muy largo
                "content_description": f"Very complex content description that might cause timeouts " * 100,
                "collaboration_type": "COMPLEX_CREATION"
            }
        
        return await self.execute_saga_scenario(session, scenario_id, payload, failure_type)
    
    async def execute_saga_scenario(self, session: aiohttp.ClientSession, scenario_id: int, 
                                   payload: Dict[str, Any], scenario_type: str) -> Dict[str, Any]:
        """Ejecutar un escenario de saga"""
        start_time = time.time()
        
        try:
            # Crear saga
            async with session.post(
                f"{BFF_BASE_URL}/api/v1/sagas/complete-affiliate-registration",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                creation_end_time = time.time()
                
                if response.status == 200:
                    saga_data = await response.json()
                    saga_id = saga_data.get("saga_id")
                    
                    # Monitorear saga hasta completarse o fallar
                    final_status = await self.monitor_saga_completion(session, saga_id)
                    
                    end_time = time.time()
                    
                    return {
                        "scenario_id": scenario_id,
                        "scenario_type": scenario_type,
                        "saga_id": saga_id,
                        "creation_successful": True,
                        "creation_latency_ms": (creation_end_time - start_time) * 1000,
                        "total_duration_ms": (end_time - start_time) * 1000,
                        "final_status": final_status.get("status"),
                        "steps_completed": final_status.get("steps_completed", 0),
                        "compensation_triggered": final_status.get("compensation_detected", False),
                        "recovery_successful": final_status.get("status") in ["COMPLETED", "COMPENSATING"],
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                else:
                    end_time = time.time()
                    error_text = await response.text()
                    
                    return {
                        "scenario_id": scenario_id,
                        "scenario_type": scenario_type,
                        "saga_id": None,
                        "creation_successful": False,
                        "error": f"HTTP {response.status}: {error_text}",
                        "total_duration_ms": (end_time - start_time) * 1000,
                        "recovery_successful": False,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    
        except Exception as e:
            end_time = time.time()
            
            return {
                "scenario_id": scenario_id,
                "scenario_type": scenario_type,
                "saga_id": None,
                "creation_successful": False,
                "error": str(e),
                "total_duration_ms": (end_time - start_time) * 1000,
                "recovery_successful": False,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def monitor_saga_completion(self, session: aiohttp.ClientSession, saga_id: str, 
                                     max_wait_seconds: int = 60) -> Dict[str, Any]:
        """Monitorear saga hasta que se complete o falle"""
        start_time = time.time()
        check_interval = 2  # segundos
        
        while (time.time() - start_time) < max_wait_seconds:
            try:
                async with session.get(
                    f"{BFF_BASE_URL}/api/v1/sagas/{saga_id}/status",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        status = data.get("status", "UNKNOWN")
                        steps = data.get("steps", [])
                        
                        # Detectar compensaciones
                        compensation_detected = any("compensate" in step.get("step_name", "") 
                                                   for step in steps)
                        
                        if status in ["COMPLETED", "FAILED"]:
                            return {
                                "status": status,
                                "steps_completed": len(steps),
                                "compensation_detected": compensation_detected,
                                "monitoring_duration_seconds": time.time() - start_time
                            }
                        
                        # Si está en COMPENSATING, esperar un poco más para ver el resultado final
                        if status == "COMPENSATING":
                            await asyncio.sleep(check_interval * 2)
                        else:
                            await asyncio.sleep(check_interval)
                    else:
                        break
                        
            except Exception as e:
                print(f"Error monitoring saga {saga_id}: {e}")
                break
        
        # Timeout alcanzado
        return {
            "status": "TIMEOUT",
            "steps_completed": 0,
            "compensation_detected": False,
            "monitoring_duration_seconds": max_wait_seconds
        }
    
    async def run_resilience_test(self) -> Dict[str, Any]:
        """Ejecutar el experimento completo de resiliencia"""
        print("Iniciando Experimento de Resiliencia de Saga...")
        print(f"   - Escenarios totales: {TOTAL_SCENARIOS}")
        print(f"   - Tasa de fallas inducidas: {FAILURE_INJECTION_RATE * 100}%")
        
        async with aiohttp.ClientSession() as session:
            scenarios = []
            
            for scenario_id in range(TOTAL_SCENARIOS):
                if random.random() < FAILURE_INJECTION_RATE:
                    # Escenario con falla inducida
                    scenario = await self.create_failing_saga(session, scenario_id)
                else:
                    # Escenario normal
                    scenario = await self.create_normal_saga(session, scenario_id)
                
                scenarios.append(scenario)
                print(f"   ✓ Escenario {scenario_id + 1}/{TOTAL_SCENARIOS} completado")
                
                # Pausa entre escenarios para no sobrecargar el sistema
                await asyncio.sleep(1)
        
        return self.analyze_resilience_results(scenarios)
    
    def analyze_resilience_results(self, scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analizar resultados del experimento de resiliencia"""
        normal_scenarios = [s for s in scenarios if s["scenario_type"] == "NORMAL"]
        failing_scenarios = [s for s in scenarios if s["scenario_type"] != "NORMAL"]
        
        # Analizar escenarios normales
        normal_successful = len([s for s in normal_scenarios if s.get("final_status") == "COMPLETED"])
        
        # Analizar escenarios con fallas
        failing_with_compensation = len([s for s in failing_scenarios if s.get("compensation_triggered", False)])
        failing_recovered = len([s for s in failing_scenarios if s.get("recovery_successful", False)])
        
        # Tiempo de recuperación promedio
        recovery_times = [s["total_duration_ms"] for s in failing_scenarios 
                         if s.get("recovery_successful", False) and s.get("total_duration_ms")]
        avg_recovery_time = sum(recovery_times) / len(recovery_times) if recovery_times else 0
        
        analysis = {
            "experiment_type": "resilience",
            "status": "COMPLETED",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "configuration": {
                "total_scenarios": TOTAL_SCENARIOS,
                "failure_injection_rate": FAILURE_INJECTION_RATE,
                "normal_scenarios": len(normal_scenarios),
                "failing_scenarios": len(failing_scenarios)
            },
            "results": {
                "normal_scenarios_analysis": {
                    "total": len(normal_scenarios),
                    "successful": normal_successful,
                    "success_rate": round(normal_successful / len(normal_scenarios) * 100, 2) if normal_scenarios else 0
                },
                "failing_scenarios_analysis": {
                    "total": len(failing_scenarios),
                    "with_compensation": failing_with_compensation,
                    "recovered_successfully": failing_recovered,
                    "compensation_rate": round(failing_with_compensation / len(failing_scenarios) * 100, 2) if failing_scenarios else 0,
                    "recovery_rate": round(failing_recovered / len(failing_scenarios) * 100, 2) if failing_scenarios else 0,
                    "avg_recovery_time_ms": round(avg_recovery_time, 2)
                },
                "overall_resilience": {
                    "total_scenarios": len(scenarios),
                    "scenarios_handled": normal_successful + failing_recovered,
                    "resilience_score": round((normal_successful + failing_recovered) / len(scenarios) * 100, 2)
                }
            },
            "hypothesis_validation": {
                "expected_normal_success_rate": 95,  # %
                "expected_failure_recovery_rate": 80,  # %
                "expected_recovery_time_max": 10000,  # ms
                "actual_normal_success_rate": round(normal_successful / len(normal_scenarios) * 100, 2) if normal_scenarios else 0,
                "actual_failure_recovery_rate": round(failing_recovered / len(failing_scenarios) * 100, 2) if failing_scenarios else 0,
                "actual_avg_recovery_time": round(avg_recovery_time, 2),
                "normal_success_met": (normal_successful / len(normal_scenarios) * 100) >= 95 if normal_scenarios else True,
                "failure_recovery_met": (failing_recovered / len(failing_scenarios) * 100) >= 80 if failing_scenarios else True,
                "recovery_time_met": avg_recovery_time <= 10000 if recovery_times else True
            },
            "detailed_scenarios": scenarios
        }
        
        # Verificar si se cumple la hipótesis
        hypothesis_met = (analysis["hypothesis_validation"]["normal_success_met"] and 
                         analysis["hypothesis_validation"]["failure_recovery_met"] and 
                         analysis["hypothesis_validation"]["recovery_time_met"])
        
        analysis["conclusion"] = {
            "hypothesis_met": hypothesis_met,
            "summary": self.generate_resilience_summary(analysis)
        }
        
        return analysis
    
    def generate_resilience_summary(self, analysis: Dict[str, Any]) -> str:
        """Generar resumen de conclusiones de resiliencia"""
        results = analysis["results"]
        hypothesis = analysis["hypothesis_validation"]
        
        if analysis["conclusion"]["hypothesis_met"]:
            return (f"HIPÓTESIS CUMPLIDA: Sistema resiliente con "
                   f"{results['normal_scenarios_analysis']['success_rate']}% éxito en escenarios normales, "
                   f"{results['failing_scenarios_analysis']['recovery_rate']}% recuperación en fallos, "
                   f"tiempo promedio de recuperación {results['failing_scenarios_analysis']['avg_recovery_time_ms']}ms")
        else:
            issues = []
            if not hypothesis["normal_success_met"]:
                issues.append(f"baja tasa de éxito normal ({hypothesis['actual_normal_success_rate']}% < 95%)")
            if not hypothesis["failure_recovery_met"]:
                issues.append(f"baja recuperación de fallos ({hypothesis['actual_failure_recovery_rate']}% < 80%)")
            if not hypothesis["recovery_time_met"]:
                issues.append(f"tiempo de recuperación alto ({hypothesis['actual_avg_recovery_time']}ms > 10000ms)")
            
            return f"HIPÓTESIS NO CUMPLIDA: {', '.join(issues)}"

async def main():
    experiment = ResilienceExperiment()
    
    print("🔬 EXPERIMENTO DE RESILIENCIA - PATRÓN SAGA")
    print("=" * 60)
    
    try:
        results = await experiment.run_resilience_test()
        
        # Guardar resultados
        with open("resilience_experiment_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        # Mostrar resumen
        print("\nRESULTADOS DEL EXPERIMENTO")
        print("=" * 40)
        print(f"Status: {results['status']}")
        print(f"Escenarios normales exitosos: {results['results']['normal_scenarios_analysis']['successful']}/{results['results']['normal_scenarios_analysis']['total']}")
        print(f"Escenarios con fallas recuperados: {results['results']['failing_scenarios_analysis']['recovered_successfully']}/{results['results']['failing_scenarios_analysis']['total']}")
        print(f"Score de resiliencia: {results['results']['overall_resilience']['resilience_score']}%")
        print(f"Tiempo promedio de recuperación: {results['results']['failing_scenarios_analysis']['avg_recovery_time_ms']}ms")
        print()
        print("VALIDACIÓN DE HIPÓTESIS")
        print("=" * 30)
        print(results['conclusion']['summary'])
        
        print(f"\nResultados guardados en: resilience_experiment_results.json")
        
    except Exception as e:
        print(f"Error en experimento: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())